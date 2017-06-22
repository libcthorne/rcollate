import ast
from functools import wraps

from flask import Flask, Response, redirect, request, url_for
from jinja2 import Environment, FileSystemLoader

from config import secrets, settings
import scheduler

TEMPLATES = Environment(loader=FileSystemLoader('templates'))

INDEX_TEMPLATE = TEMPLATES.get_template("index.html")
JOBS_INDEX_TEMPLATE = TEMPLATES.get_template("jobs_index.html")
JOBS_SHOW_TEMPLATE = TEMPLATES.get_template("jobs_show.html")
JOBS_EDIT_TEMPLATE = TEMPLATES.get_template("jobs_edit.html")
JOBS_NEW_TEMPLATE = TEMPLATES.get_template("jobs_new.html")

app = Flask(__name__)

def check_auth(username, password):
    return username == secrets['admin_username'] and password == secrets['admin_password']

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route("/jobs/")
@requires_admin
def jobs_index():
    return JOBS_INDEX_TEMPLATE.render(jobs=scheduler.jobs)

@app.route("/jobs/<string:job_id>/")
def jobs_show(job_id):
    if not scheduler.is_valid_job_id(job_id):
        return "Job %s not found" % job_id

    return JOBS_SHOW_TEMPLATE.render(job=scheduler.get_job_by_id(job_id))

@app.route("/jobs/<string:job_id>/", methods=['POST'])
def jobs_update(job_id):
    if not scheduler.is_valid_job_id(job_id):
        return "Job %s not found" % job_id

    subreddit = request.form['subreddit']
    target_email = request.form['target_email']
    cron_trigger = ast.literal_eval(request.form['cron_trigger'])

    scheduler.update_job(
        job_id=job_id,
        subreddit=subreddit,
        target_email=target_email,
        cron_trigger=cron_trigger
    )

    return redirect(url_for('jobs_show', job_id=job_id))

@app.route("/jobs/<string:job_id>/edit/")
def jobs_edit(job_id):
    if not scheduler.is_valid_job_id(job_id):
        return "Job %s not found" % job_id

    return JOBS_EDIT_TEMPLATE.render(job=scheduler.get_job_by_id(job_id))

@app.route("/jobs/new/")
def jobs_new():
    return JOBS_NEW_TEMPLATE.render()

@app.route("/jobs/", methods=['POST'])
def jobs_create():
    subreddit = request.form['subreddit']
    target_email = request.form['target_email']
    cron_trigger = ast.literal_eval(request.form['cron_trigger'])

    job = scheduler.create_job(
        subreddit=subreddit,
        target_email=target_email,
        cron_trigger=cron_trigger
    )

    return redirect(url_for('jobs_show', job_id=job['_id']))

@app.route("/jobs/<string:job_id>/delete/", methods=['POST'])
def jobs_delete(job_id):
    if not scheduler.is_valid_job_id(job_id):
        return "Job %s not found" % job_id

    scheduler.delete_job(job_id)

    return redirect(url_for("jobs_new"))

@app.route("/")
def index():
    return jobs_new()

def get_full_job_view_url(job_id):
    with app.test_request_context():
        return "{}{}".format(
            settings['app_url'],
            url_for(
                "jobs_show",
                job_id=job_id,
            )
        )

scheduler.init(
    get_full_job_view_url_fn=get_full_job_view_url,
)
scheduler.start()
