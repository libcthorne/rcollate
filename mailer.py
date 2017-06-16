import emails
import json
import logging
import praw
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from jinja2 import Environment, FileSystemLoader

TEMPLATES = Environment(loader=FileSystemLoader('.'))
HTML_EMAIL_TEMPLATE = TEMPLATES.get_template("email_body.html.j2")

logger = None
scheduler = None
settings = None
secrets = None
jobs = None

def init_logger():
    global logger

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Log line format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Console output handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Log file handler
    fh = logging.FileHandler('rcollate.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

def load_config():
    global settings
    global secrets

    try:
        with open('settings.json') as f:
            settings = json.load(f)
    except IOError:
        logger.error("settings.json missing")
        sys.exit(1)

    try:
        with open('secrets.json') as f:
            secrets = json.load(f)
    except IOError:
        logger.error("secrets.json missing (see example_secrets.json for a template)")
        sys.exit(1)

def load_jobs():
    global jobs

    try:
        with open('jobs.json') as f:
            jobs = json.load(f)
    except IOError:
        logger.error("jobs.json missing (see example_jobs.json for a template)")
        sys.exit(1)

def save_jobs():
    try:
        serialized_jobs = [
            {
                k: job[k]
                for k in job
                if k[0] != '_'
            }
            for job in jobs
        ]

        with open('jobs.json', 'w') as f:
            json.dump(serialized_jobs, f, indent=4)
    except IOError:
        logger.error("Failed to save jobs to jobs.json")
        sys.exit(1)

def send_email(job):
    logger.info("Send /r/{} email to {}".format(job["subreddit"], job["target_email"]))

    reddit = praw.Reddit(
        client_id=secrets["client_id"],
        client_secret=secrets["client_secret"],
        user_agent=settings["user_agent"]
    )

    subreddit = reddit.subreddit(job["subreddit"])

    message_body_html = HTML_EMAIL_TEMPLATE.render(
        r_threads=subreddit.top(
            job["time_filter"],
            limit=job["thread_limit"]
        ),
    )

    message = emails.html(
        html=message_body_html,
        subject="Top threads in /r/{}".format(job["subreddit"]),
        mail_from=(
            settings["sender_name"], settings["sender_email"]
        )
    )

    r = message.send(
        to=job["target_email"],
        smtp={'host': settings["smtp_host"], 'timeout': settings["smtp_timeout"]}
    )

    if r.status_code == 250:
        logger.info("Sent /r/{} email to {}".format(
            job["subreddit"], job["target_email"]
        ))
    else:
        logger.error("Error sending /r/{} email to {}: status_code={}, err={}".format(
            job["subreddit"], job["target_email"], r.status_code, r.error
        ))

def is_valid_job_id(job_id):
    return job_id >= 1 and job_id <= len(jobs)

def get_job_by_id(job_id):
    return jobs[job_id-1]

def update_job(job_id, subreddit, target_email, cron_trigger):
    job = get_job_by_id(job_id)
    job['subreddit'] = subreddit
    job['target_email'] = target_email
    job['cron_trigger'] = cron_trigger
    job['_handle'].reschedule('cron', **cron_trigger)

    save_jobs()

def start(block=False):
    global scheduler

    init_logger()

    load_config()
    load_jobs()

    scheduler_cls = BlockingScheduler if block else BackgroundScheduler
    scheduler = scheduler_cls()

    for index, job in enumerate(jobs):
        job_id = index + 1
        job['_id'] = job_id
        job['_handle'] = scheduler.add_job(
           send_email, 'cron', [job], **job["cron_trigger"]
        )

    scheduler.start()

if __name__ == "__main__":
    start(block=True)
