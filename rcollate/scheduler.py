import hashlib
import json
import praw
import random
import string

from apscheduler.schedulers.background import BackgroundScheduler
from mailer import Mailer

from config import settings, secrets
import logs
import resources

JOBS_FILE = "db/jobs.json"

JOB_DEFAULTS = {
    "thread_limit": 10,
    "time_filter": "day",
}

JOB_ID_LENGTH = 12

jobs = None
mailer = None
scheduler = None
logger = logs.get_logger()

def read_jobs():
    serialized_jobs = resources.read_json_file(JOBS_FILE, required=False, default=[])
    jobs = {}

    for job_id, job in serialized_jobs.items():
        job['_id'] = job_id
        jobs[job_id] = job

    return jobs

def write_jobs():
    try:
        serialized_jobs = {
            job_id: {
                k: job[k]
                for k in job
                if k[0] != '_'
            }
            for job_id, job in jobs.items()
        }

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

def create_job(subreddit, target_email, cron_trigger):
    job = JOB_DEFAULTS.copy()
    job['subreddit'] = subreddit
    job['target_email'] = target_email
    job['cron_trigger'] = cron_trigger
    job['_handle'] = scheduler.add_job(
       run_job, 'cron', [job], **job["cron_trigger"]
    )

    job_id = get_new_job_id()
    job['_id'] = job_id
    jobs[job_id] = job

    write_jobs()

    return job

def update_job(job_id, subreddit, target_email, cron_trigger):
    job = get_job_by_id(job_id)
    job['subreddit'] = subreddit
    job['target_email'] = target_email
    job['cron_trigger'] = cron_trigger
    job['_handle'].reschedule('cron', **cron_trigger)

    write_jobs()

def delete_job(job_id):
    job = jobs[job_id]
    job['_handle'].remove()
    del jobs[job_id]

    write_jobs()

def get_job_key(job_id):
    return hashlib.sha1(jobs[job_id]['target_email'].encode('utf-8')).hexdigest()

def can_view_job(job_id, key):
    return is_valid_job_id(job_id) and key == get_job_key(job_id)

def is_valid_job_id(job_id):
    return job_id in jobs

def get_job_by_id(job_id):
    return jobs[job_id]

def get_new_job_id():
    while True:
        random_id = ''.join(
            random.SystemRandom().choice(
                string.ascii_lowercase + string.ascii_uppercase + string.digits
            )
            for _ in range(JOB_ID_LENGTH)
        )

        if random_id not in jobs:
            return random_id

def start():
    global jobs
    global mailer
    global scheduler

    jobs = read_jobs()
    mailer = Mailer(
        smtp_host=settings["smtp_host"],
        smtp_timeout=settings["smtp_timeout"],
        sender_name=settings["sender_name"],
        sender_email=settings["sender_email"],
    )
    scheduler = BackgroundScheduler()

    for job in jobs.values():
        job['_handle'] = scheduler.add_job(
           run_job, 'cron', [job], **job["cron_trigger"]
        )

    scheduler.start()
