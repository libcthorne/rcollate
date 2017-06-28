import json
from pathlib import Path
import praw
import random
import string
import sqlite3

from apscheduler.schedulers.background import BackgroundScheduler

from rcollate import logs, resources
from rcollate.config import settings, secrets
from rcollate.mailer import Mailer
import rcollate.reddit as reddit

JOBS_DB_FILE = "db/jobs.db"
JOBS_DB_SCHEMA = "db/jobs_schema.sql"

JOB_DEFAULTS = {
    "thread_limit": 10,
    "time_filter": "day",
}

JOB_ID_LENGTH = 20

jobs = None
mailer = None
scheduler = None
logger = logs.get_logger()

def db_init():
    if Path(JOBS_DB_FILE).is_file():
        logger.info("DB already initialized")
        return

    logger.info("Initializing DB")

    with open(JOBS_DB_SCHEMA) as f:
        conn = sqlite3.connect(JOBS_DB_FILE)
        with conn:
            conn.executescript(f.read())
        conn.close()

def db_read_jobs():
    rows = []
    conn = sqlite3.connect(JOBS_DB_FILE)
    conn.row_factory = sqlite3.Row
    with conn:
        c = conn.execute("SELECT * FROM jobs")
        rows = c.fetchall()
    conn.close()

    jobs = {}

    for row in rows:
        job_key = row['job_key']
        job = {
            '_id': job_key,
            'thread_limit': row['thread_limit'],
            'target_email': row['target_email'],
            'time_filter': row['time_filter'],
            'cron_trigger': json.loads(row['cron_trigger']),
            'subreddit': row['subreddit'],
        }
        jobs[job_key] = job

    return jobs

def db_insert_job(job):
    conn = sqlite3.connect(JOBS_DB_FILE)
    with conn:
        conn.execute(
            """
            INSERT INTO jobs (
                job_key,
                thread_limit,
                target_email,
                time_filter,
                cron_trigger,
                subreddit
            ) VALUES (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )
            """,
            (
                job['_id'],
                job['thread_limit'],
                job['target_email'],
                job['time_filter'],
                json.dumps(job['cron_trigger']),
                job['subreddit']
            )
        )
    conn.close()

def db_update_job(job):
    conn = sqlite3.connect(JOBS_DB_FILE)
    with conn:
        conn.execute(
            """
            UPDATE jobs
            SET
                job_key = ?,
                thread_limit = ?,
                target_email = ?,
                time_filter = ?,
                cron_trigger = ?,
                subreddit = ?
            WHERE
                job_key = ?
            """,
            (
                job['_id'],
                job['thread_limit'],
                job['target_email'],
                job['time_filter'],
                json.dumps(job['cron_trigger']),
                job['subreddit'],
                job['_id'],
            )
        )
    conn.close()

def db_delete_job(job):
    conn = sqlite3.connect(JOBS_DB_FILE)
    with conn:
        conn.execute(
            "DELETE FROM jobs WHERE job_key = ?",
            (
                job['_id'],
            )
        )
    conn.close()

def run_job(job):
    mailer.send_threads(
        r_threads=reddit.top_subreddit_threads(
            job["subreddit"],
            job["time_filter"],
            job["thread_limit"],
        ),
        target_email=job["target_email"],
        subreddit=job["subreddit"],
        job_view_url=get_full_job_view_url(job['_id'])
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

    db_insert_job(job)

    return job

def update_job(job_id, subreddit, target_email, cron_trigger):
    job = get_job_by_id(job_id)
    job['subreddit'] = subreddit
    job['target_email'] = target_email
    job['cron_trigger'] = cron_trigger
    job['_handle'].reschedule('cron', **cron_trigger)

    db_update_job(job)

def delete_job(job_id):
    job = jobs[job_id]
    job['_handle'].remove()
    del jobs[job_id]

    db_delete_job(job)

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

def init(get_full_job_view_url_fn):
    global get_full_job_view_url
    get_full_job_view_url = get_full_job_view_url_fn

    db_init()

def start():
    global jobs
    global mailer
    global scheduler

    jobs = db_read_jobs()
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
