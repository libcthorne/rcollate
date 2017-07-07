from functools import wraps

from flask import (
    Flask, Response,
    flash, g, redirect, render_template, request, url_for,
)
from flask_socketio import SocketIO, emit
from jinja2 import Environment, FileSystemLoader

from rcollate import scheduler
from rcollate.config import secrets, settings
from rcollate.models import Job
import rcollate.db as db
import rcollate.reddit as reddit
import rcollate.forms as forms

DEFAULT_CRON_TRIGGER = {'hour': 6}

app = Flask('rcollate')
app.config['SECRET_KEY'] = secrets['session_secret_key']

socketio = SocketIO(app)

def get_db_conn():
    if not hasattr(g, 'db_conn'):
        g.db_conn = db.open_conn()
    return g.db_conn

@app.teardown_appcontext
def close_db_conn(exception):
    if hasattr(g, 'db_conn'):
        g.db_conn.close()

def check_auth(username, password):
    return username == secrets['admin_username'] and password == secrets['admin_password']

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    "Could not verify your access level for that URL.\n"
    "You have to login with proper credentials", 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def create_job(subreddit, target_email, cron_trigger):
    job = Job(
        subreddit=subreddit,
        target_email=target_email,
        cron_trigger=DEFAULT_CRON_TRIGGER,
    )

    db.insert_job(get_db_conn(), job)
    scheduler.schedule_job(job)

    return job

def update_job(job_key, subreddit, target_email, cron_trigger):
    job = db.get_job(get_db_conn(), job_key)
    job.subreddit = subreddit
    job.target_email = target_email
    job.cron_trigger = cron_trigger

    db.update_job(get_db_conn(), job)
    scheduler.reschedule_job(job)

def delete_job(job_key):
    job = db.get_job(get_db_conn(), job_key)
    scheduler.unschedule_job(job)
    db.delete_job(get_db_conn(), job_key)

def run_job(job_key):
    job = db.get_job(get_db_conn(), job_key)
    scheduler.run_job(job)

@app.route("/jobs/")
@requires_admin
def jobs_index():
    return render_template('jobs_index.html', jobs=db.get_jobs(get_db_conn()))

@app.route('/jobs/<string:job_key>/')
def jobs_show(job_key):
    if not db.is_valid_job_key(get_db_conn(), job_key):
        return "Job %s not found" % job_key

    return render_template('jobs_show.html', job=db.get_job(get_db_conn(), job_key))

@app.route('/jobs/<string:job_key>/', methods=['POST'])
@app.route('/jobs/<string:job_key>/edit/', methods=['GET', 'POST'])
def jobs_edit(job_key):
    if not db.is_valid_job_key(get_db_conn(), job_key):
        return "Job %s not found" % job_key

    if request.form:
        form = forms.JobForm(request.form)
    else:
        job = db.get_job(get_db_conn(), job_key)
        form = forms.JobForm(
            subreddit=job.subreddit,
            target_email=job.target_email,
        )

    if form.validate_on_submit():
        update_job(
            job_key=job_key,
            subreddit=form.subreddit.data,
            target_email=form.target_email.data,
            cron_trigger=DEFAULT_CRON_TRIGGER,
        )

        return redirect(url_for('jobs_show', job_key=job_key))

    return render_template('jobs_edit.html', form=form)

@app.route('/', methods=['GET', 'POST'])
@app.route('/jobs/', methods=['POST'])
@app.route('/jobs/new/', methods=['GET', 'POST'])
def jobs_new():
    form = forms.JobForm(request.form)

    if form.validate_on_submit():
        job = create_job(
            subreddit=form.subreddit.data,
            target_email=form.target_email.data,
            cron_trigger=DEFAULT_CRON_TRIGGER,
        )

        return redirect(url_for('jobs_show', job_key=job.job_key))

    return render_template('jobs_new.html', form=form)

@app.route('/jobs/<string:job_key>/delete/', methods=['POST'])
def jobs_delete(job_key):
    if not db.is_valid_job_key(get_db_conn(), job_key):
        return "Job %s not found" % job_key

    delete_job(job_key)

    return redirect(url_for('jobs_new'))

@app.route('/jobs/<string:job_key>/run/', methods=['POST'])
def jobs_run(job_key):
    if not db.is_valid_job_key(get_db_conn(), job_key):
        return "Job %s not found" % job_key

    run_job(job_key)

    return redirect(url_for('jobs_show', job_key=job_key))

@socketio.on('subreddit_search_request')
def subreddit_search(message):
    subreddit = message['subreddit']

    matches = sorted([
        r.display_name
        for r in reddit.subreddit_search(subreddit)
    ], key=len)

    emit('subreddit_search_response', {
        'subreddit': subreddit,
        'matches': matches,
    })

def _get_job_by_job_key(job_key):
    db_conn = db.open_conn()
    job = db.get_job(db_conn, job_key)
    db.close_conn(db_conn)
    return job

def _get_job_url_by_job_key(job_key):
    with app.test_request_context():
        return '{}{}'.format(
            settings['app_url'],
            url_for(
                'jobs_show',
                job_key=job_key,
            )
        )

db.init()

db_conn = db.open_conn()
scheduler.start(
    initial_jobs=db.get_jobs(db_conn).values(),
    get_job_by_job_key_fn=_get_job_by_job_key,
    get_job_url_by_job_key_fn=_get_job_url_by_job_key,
)
db.close_conn(db_conn)
