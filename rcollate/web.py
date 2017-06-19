import ast
from functools import wraps

from flask import Flask, Response, redirect, request, url_for
from jinja2 import Environment, FileSystemLoader

import main as rcollate
import resources

WEB_ADMIN_FILE = "config/web_admin.json"

TEMPLATES = Environment(loader=FileSystemLoader('templates'))
INDEX_TEMPLATE = TEMPLATES.get_template("index.html.j2")
JOBS_INDEX_TEMPLATE = TEMPLATES.get_template("jobs_index.html.j2")
JOBS_SHOW_TEMPLATE = TEMPLATES.get_template("jobs_show.html.j2")
JOBS_EDIT_TEMPLATE = TEMPLATES.get_template("jobs_edit.html.j2")
JOBS_NEW_TEMPLATE = TEMPLATES.get_template("jobs_new.html.j2")

web_admin = resources.read_json_file(WEB_ADMIN_FILE)

app = Flask(__name__)

def check_auth(username, password):
    return username == web_admin['username'] and password == web_admin['password']

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
    return JOBS_INDEX_TEMPLATE.render(jobs=rcollate.jobs)

@app.route("/jobs/<int:job_id>/")
def jobs_show(job_id):
    if not rcollate.is_valid_job_id(job_id):
        return "Job %d not found" % job_id

    return JOBS_SHOW_TEMPLATE.render(job=rcollate.get_job_by_id(job_id))

@app.route("/jobs/<int:job_id>/", methods=['POST'])
def jobs_update(job_id):
    if not rcollate.is_valid_job_id(job_id):
        return "Job %d not found" % job_id

    subreddit = request.form['subreddit']
    target_email = request.form['target_email']
    cron_trigger = ast.literal_eval(request.form['cron_trigger'])

    rcollate.update_job(
        job_id=job_id,
        subreddit=subreddit,
        target_email=target_email,
        cron_trigger=cron_trigger
    )

    return jobs_show(job_id)

@app.route("/jobs/<int:job_id>/edit/")
def jobs_edit(job_id):
    if not rcollate.is_valid_job_id(job_id):
        return "Job %d not found" % job_id

    return JOBS_EDIT_TEMPLATE.render(job=rcollate.get_job_by_id(job_id))

@app.route("/jobs/new/")
def jobs_new():
    return JOBS_NEW_TEMPLATE.render()

@app.route("/jobs/", methods=['POST'])
def jobs_create():
    subreddit = request.form['subreddit']
    target_email = request.form['target_email']
    cron_trigger = ast.literal_eval(request.form['cron_trigger'])

    rcollate.create_job(
        subreddit=subreddit,
        target_email=target_email,
        cron_trigger=cron_trigger
    )

    return jobs_index()

@app.route("/jobs/<int:job_id>/delete/", methods=['POST'])
def jobs_delete(job_id):
    if not rcollate.is_valid_job_id(job_id):
        return "Job %d not found" % job_id

    rcollate.delete_job(job_id)

    return redirect(url_for("jobs_index"))

@app.route("/")
def index():
    return INDEX_TEMPLATE.render()

rcollate.start()
