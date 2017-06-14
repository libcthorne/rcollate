import emails
import logging
import json
import praw
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from jinja2 import Environment, FileSystemLoader

HTML_EMAIL_TEMPLATE = Environment(
    loader=FileSystemLoader('.')
).get_template("email_body.html.j2")

logger = None

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

def load_config_files():
    global settings
    global secrets
    global jobs

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

    try:
        with open('jobs.json') as f:
            jobs = json.load(f)
    except IOError:
        logger.error("jobs.json missing (see example_jobs.json for a template)")
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
        subject="/r/{}".format(job["subreddit"]),
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

def run():
    init_logger()

    load_config_files()

    scheduler = BlockingScheduler()

    for job in jobs:
        scheduler.add_job(send_email, 'cron', [job], **job["cron_trigger"])

    scheduler.start()

if __name__ == "__main__":
    run()
