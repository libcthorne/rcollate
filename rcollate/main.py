import json
import praw
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from mailer import Mailer

import logs
import resources

SETTINGS_FILE = "config/settings.json"
SECRETS_FILE = "config/secrets.json"
JOBS_FILE = "db/jobs.json"

settings = None
secrets = None
jobs = None
mailer = None

logger = logs.get_logger()

def read_jobs():
    jobs = resources.read_json_file(JOBS_FILE, required=False, default=[])

    for index, job in enumerate(jobs):
        job_id = index + 1
        job['_id'] = job_id

    return jobs

def write_jobs():
    try:
        serialized_jobs = [
            {
                k: job[k]
                for k in job
                if k[0] != '_'
            }
            for job in jobs
        ]

        with open(JOBS_FILE, 'w') as f:
            json.dump(serialized_jobs, f, indent=4)
    except IOError:
        logger.error("Failed to save jobs to %s", JOBS_FILE)


def run_job(job):
    reddit = praw.Reddit(
        client_id=secrets["client_id"],
        client_secret=secrets["client_secret"],
        user_agent=settings["user_agent"]
    )

    subreddit = reddit.subreddit(job["subreddit"])

    mailer.send_threads(
        r_threads=subreddit.top(
            job["time_filter"],
            limit=job["thread_limit"]
        ),
        target_email=job["target_email"],
        subreddit=job["subreddit"],
    )

def update_job(job_id, subreddit, target_email, cron_trigger):
    job = get_job_by_id(job_id)
    job['subreddit'] = subreddit
    job['target_email'] = target_email
    job['cron_trigger'] = cron_trigger
    job['_handle'].reschedule('cron', **cron_trigger)

    write_jobs()

def is_valid_job_id(job_id):
    return job_id >= 1 and job_id <= len(jobs)

def get_job_by_id(job_id):
    return jobs[job_id-1]

def start(block=False):
    global settings
    global secrets
    global jobs
    global mailer

    settings = resources.read_json_file(SETTINGS_FILE)
    secrets = resources.read_json_file(SECRETS_FILE)
    jobs = read_jobs()
    mailer = Mailer(
        smtp_host=settings["smtp_host"],
        smtp_timeout=settings["smtp_timeout"],
        sender_name=settings["sender_name"],
        sender_email=settings["sender_email"],
    )

    scheduler_cls = BlockingScheduler if block else BackgroundScheduler
    scheduler = scheduler_cls()

    for index, job in enumerate(jobs):
        job['_handle'] = scheduler.add_job(
           run_job, 'cron', [job], **job["cron_trigger"]
        )

    scheduler.start()

if __name__ == "__main__":
    start(block=True)
