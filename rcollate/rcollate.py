import ast
from functools import wraps
import re

from flask import (
    Flask, Response,
    flash, g, redirect, render_template, request, url_for,
)
from flask_socketio import SocketIO, emit
from jinja2 import Environment, FileSystemLoader

from rcollate import scheduler
from rcollate.config import secrets, settings
import rcollate.db as db
import rcollate.reddit as reddit

DEFAULT_CRON_TRIGGER = {'hour': 6}

JOB_DEFAULTS = {
    'thread_limit': 10,
    'time_filter': 'day',
}

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

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

def validate_job_fields(subreddit, target_email):
    if subreddit is None or len(subreddit) == 0:
        return "Subreddit is missing"

    if target_email is None or len(target_email) == 0:
        return "Email is missing"

    if not reddit.subreddit_exists(subreddit):
        return "Subreddit not found"

    if not EMAIL_REGEX.match(target_email):
        return "Email is invalid"

def create_job(subreddit, target_email, cron_trigger):
    data = JOB_DEFAULTS.copy()
    data['subreddit'] = subreddit
    data['target_email'] = target_email
    data['cron_trigger'] = cron_trigger

    job = db.insert_job(get_db_conn(), data)
    scheduler.schedule_job(job)

    return job

def update_job(job_key, subreddit, target_email, cron_trigger):
    job = db.get_job(get_db_conn(), job_key)
    job['subreddit'] = subreddit
    job['target_email'] = target_email
    job['cron_trigger'] = cron_trigger

    db.update_job(get_db_conn(), job_key, job)
    scheduler.reschedule_job(job)

def delete_job(job_key):
    job = db.get_job(get_db_conn(), job_key)
    scheduler.unschedule_job(job)
    db.delete_job(get_db_conn(), job_key)

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
def jobs_update(job_key):
    if not db.is_valid_job_key(get_db_conn(), job_key):
        return "Job %s not found" % job_key

    subreddit = request.form.get('subreddit')
    target_email = request.form.get('target_email')

    error = validate_job_fields(subreddit, target_email)
    if error is not None:
        flash(error)
        return redirect(url_for('jobs_edit', job_key=job_key))

    update_job(
        job_key=job_key,
        subreddit=subreddit,
        target_email=target_email,
        cron_trigger=DEFAULT_CRON_TRIGGER,
    )

    return redirect(url_for('jobs_show', job_key=job_key))

@app.route('/jobs/<string:job_key>/edit/')
def jobs_edit(job_key):
    if not db.is_valid_job_key(get_db_conn(), job_key):
        return "Job %s not found" % job_key

    return render_template('jobs_edit.html', job=db.get_job(get_db_conn(), job_key))

@app.route('/jobs/new/')
def jobs_new():
    return render_template('jobs_new.html')

@app.route("/jobs/", methods=['POST'])
def jobs_create():
    subreddit = request.form.get('subreddit')
    target_email = request.form.get('target_email')

    error = validate_job_fields(subreddit, target_email)
    if error is not None:
        flash(error)
        return redirect(url_for('jobs_new'))

    job = create_job(
        subreddit=subreddit,
        target_email=target_email,
        cron_trigger=DEFAULT_CRON_TRIGGER,
    )

    return redirect(url_for('jobs_show', job_key=job['job_key']))

@app.route('/jobs/<string:job_key>/delete/', methods=['POST'])
def jobs_delete(job_key):
    if not db.is_valid_job_key(get_db_conn(), job_key):
        return "Job %s not found" % job_key

    delete_job(job_key)

    return redirect(url_for('jobs_new'))

@app.route("/")
def index():
    return jobs_new()

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

db_conn = db.open_conn()
scheduler.start(
    initial_jobs=db.get_jobs(db_conn).values(),
    get_job_by_job_key_fn=_get_job_by_job_key,
    get_job_url_by_job_key_fn=_get_job_url_by_job_key,
)
db.close_conn(db_conn)
