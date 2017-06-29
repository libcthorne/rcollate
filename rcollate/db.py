import json
from pathlib import Path
import random
import string
import sqlite3

JOBS_DB_FILE = "db/jobs.db"
JOBS_DB_SCHEMA = "db/jobs_schema.sql"
JOB_KEY_LENGTH = 20

def init():
    if Path(JOBS_DB_FILE).is_file():
        logger.info("DB already initialized")
        return

    logger.info("Initializing DB")

    with open(JOBS_DB_SCHEMA) as f:
        conn = sqlite3.connect(JOBS_DB_FILE)
        with conn:
            conn.executescript(f.read())
        conn.close()

def get_job(job_key):
    conn = sqlite3.connect(JOBS_DB_FILE)
    conn.row_factory = sqlite3.Row
    with conn:
        c = conn.execute(
            """
            SELECT * FROM jobs
            WHERE job_key = ?
            """,
            (
                job_key,
            )
        )
        row = c.fetchone()
    conn.close()

    if row:
        return {
            'job_key': row['job_key'],
            'thread_limit': row['thread_limit'],
            'target_email': row['target_email'],
            'time_filter': row['time_filter'],
            'cron_trigger': json.loads(row['cron_trigger']),
            'subreddit': row['subreddit'],
        }

def get_jobs():
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
            'job_key': job_key,
            'thread_limit': row['thread_limit'],
            'target_email': row['target_email'],
            'time_filter': row['time_filter'],
            'cron_trigger': json.loads(row['cron_trigger']),
            'subreddit': row['subreddit'],
        }
        jobs[job_key] = job

    return jobs

def insert_job(data):
    print("Getting key")
    job_key = get_new_job_key()
    print("Got key")
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
                job_key,
                data['thread_limit'],
                data['target_email'],
                data['time_filter'],
                json.dumps(data['cron_trigger']),
                data['subreddit']
            )
        )
    conn.close()

    return get_job(job_key)

def update_job(job_key, data):
    conn = sqlite3.connect(JOBS_DB_FILE)
    with conn:
        conn.execute(
            """
            UPDATE jobs
            SET
                thread_limit = ?,
                target_email = ?,
                time_filter = ?,
                cron_trigger = ?,
                subreddit = ?
            WHERE
                job_key = ?
            """,
            (
                data['thread_limit'],
                data['target_email'],
                data['time_filter'],
                json.dumps(data['cron_trigger']),
                data['subreddit'],
                job_key,
            )
        )
    conn.close()

    return get_job(job_key)

def delete_job(job_key):
    conn = sqlite3.connect(JOBS_DB_FILE)
    with conn:
        conn.execute(
            "DELETE FROM jobs WHERE job_key = ?",
            (
                job_key,
            )
        )
    conn.close()

def is_valid_job_key(job_key):
    # TODO: replace with EXISTS query
    return get_job(job_key) is not None

def get_new_job_key():
    while True:
        random_key = ''.join(
            random.SystemRandom().choice(
                string.ascii_lowercase + string.ascii_uppercase + string.digits
            )
            for _ in range(JOB_KEY_LENGTH)
        )

        if not is_valid_job_key(random_key):
            return random_key
