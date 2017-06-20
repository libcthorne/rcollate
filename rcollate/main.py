import ast
from functools import wraps

from flask import Flask, Response, redirect, request, url_for
from jinja2 import Environment, FileSystemLoader

from config import secrets
import scheduler

TEMPLATES = Environment(loader=FileSystemLoader('templates'))
TEMPLATES.globals.update(get_job_key=scheduler.get_job_key)

INDEX_TEMPLATE = TEMPLATES.get_template("index.html.j2")
JOBS_INDEX_TEMPLATE = TEMPLATES.get_template("jobs_index.html.j2")
JOBS_SHOW_TEMPLATE = TEMPLATES.get_template("jobs_show.html.j2")
JOBS_EDIT_TEMPLATE = TEMPLATES.get_template("jobs_edit.html.j2")
JOBS_NEW_TEMPLATE = TEMPLATES.get_template("jobs_new.html.j2")

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
    if not scheduler.can_view_job(job_id, request.args.get('key')):
        return "Job %s not found" % job_id

    return JOBS_SHOW_TEMPLATE.render(job=scheduler.get_job_by_id(job_id))

@app.route("/jobs/<string:job_id>/", methods=['POST'])
def jobs_update(job_id):
    if not scheduler.can_view_job(job_id, request.args.get('key')):
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

    return redirect(url_for('jobs_show', job_id=job_id, key=scheduler.get_job_key(job_id)))

@app.route("/jobs/<string:job_id>/edit/")
def jobs_edit(job_id):
    if not scheduler.can_view_job(job_id, request.args.get('key')):
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

    return redirect(url_for('jobs_show', job_id=job['_id'], key=scheduler.get_job_key(job['_id'])))

@app.route("/jobs/<string:job_id>/delete/", methods=['POST'])
def jobs_delete(job_id):
    if not scheduler.can_view_job(job_id, request.args.get('key')):
        return "Job %s not found" % job_id

    scheduler.delete_job(job_id)

    return redirect(url_for("jobs_index"))

@app.route("/")
def index():
    return jobs_new()

scheduler.start()
