import ast
import mailer

from flask import Flask, request
from jinja2 import Environment, FileSystemLoader

TEMPLATES = Environment(loader=FileSystemLoader('.'))
INDEX_TEMPLATE = TEMPLATES.get_template("index.html.j2")
JOBS_INDEX_TEMPLATE = TEMPLATES.get_template("jobs_index.html.j2")
JOBS_SHOW_TEMPLATE = TEMPLATES.get_template("jobs_show.html.j2")
JOBS_EDIT_TEMPLATE = TEMPLATES.get_template("jobs_edit.html.j2")

app = Flask(__name__)

@app.route("/jobs/")
def jobs_index():
    return JOBS_INDEX_TEMPLATE.render(jobs=mailer.jobs)

@app.route("/jobs/<int:job_id>/")
def jobs_show(job_id):
    if not mailer.is_valid_job_id(job_id):
        return "Job %d not found" % job_id

    return JOBS_SHOW_TEMPLATE.render(job=mailer.get_job_by_id(job_id))

@app.route("/jobs/<int:job_id>/", methods=['POST'])
def jobs_update(job_id):
    if not mailer.is_valid_job_id(job_id):
        return "Job %d not found" % job_id

    subreddit = request.form['subreddit']
    target_email = request.form['target_email']
    cron_trigger = ast.literal_eval(request.form['cron_trigger'])

    mailer.update_job(
        job_id=job_id,
        subreddit=subreddit,
        target_email=target_email,
        cron_trigger=cron_trigger
    )

    return jobs_show(job_id)

@app.route("/jobs/<int:job_id>/edit/")
def jobs_edit(job_id):
    if not mailer.is_valid_job_id(job_id):
        return "Job %d not found" % job_id

    return JOBS_EDIT_TEMPLATE.render(job=mailer.get_job_by_id(job_id))

@app.route("/")
def index():
    return INDEX_TEMPLATE.render()

mailer.start()
