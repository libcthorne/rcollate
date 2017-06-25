import ast
from functools import wraps
import re

from flask import (
    Flask, Response,
    flash, redirect, render_template, request, url_for,
)
from jinja2 import Environment, FileSystemLoader

from rcollate import scheduler
from rcollate.config import secrets, settings
import rcollate.reddit as reddit

DEFAULT_CRON_TRIGGER = {"hour": 6}

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

app = Flask('rcollate')
app.config['SECRET_KEY'] = secrets['session_secret_key']

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

def validate_job_fields(subreddit, target_email):
    if subreddit is None or len(subreddit) == 0:
        return "Subreddit is missing"

    if target_email is None or len(target_email) == 0:
        return "Email is missing"

    if not reddit.subreddit_exists(subreddit):
        return "Subreddit not found"

    if not EMAIL_REGEX.match(target_email):
        return "Email is invalid"

@app.route("/jobs/")
@requires_admin
def jobs_index():
    return render_template('jobs_index.html', jobs=scheduler.jobs)

@app.route("/jobs/<string:job_id>/")
def jobs_show(job_id):
    if not scheduler.is_valid_job_id(job_id):
        return "Job %s not found" % job_id

    return render_template('jobs_show.html', job=scheduler.get_job_by_id(job_id))

@app.route("/jobs/<string:job_id>/", methods=['POST'])
def jobs_update(job_id):
    if not scheduler.is_valid_job_id(job_id):
        return "Job %s not found" % job_id

    subreddit = request.form.get('subreddit')
    target_email = request.form.get('target_email')

    error = validate_job_fields(subreddit, target_email)
    if error is not None:
        flash(error)
        return redirect(url_for('jobs_edit', job_id=job_id))

    scheduler.update_job(
        job_id=job_id,
        subreddit=subreddit,
        target_email=target_email,
        cron_trigger=DEFAULT_CRON_TRIGGER,
    )

    return redirect(url_for('jobs_show', job_id=job_id))

@app.route("/jobs/<string:job_id>/edit/")
def jobs_edit(job_id):
    if not scheduler.is_valid_job_id(job_id):
        return "Job %s not found" % job_id

    return render_template('jobs_edit.html', job=scheduler.get_job_by_id(job_id))

@app.route("/jobs/new/")
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

    job = scheduler.create_job(
        subreddit=subreddit,
        target_email=target_email,
        cron_trigger=DEFAULT_CRON_TRIGGER,
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
