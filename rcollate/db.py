import json
from pathlib import Path
import random
import string
import sqlite3

from rcollate import logs

JOBS_DB_FILE = 'db/jobs.db'
JOBS_DB_SCHEMA = 'db/jobs_schema.sql'
JOB_KEY_LENGTH = 20

logger = logs.get_logger()

def open_conn():
    db_conn = sqlite3.connect(JOBS_DB_FILE)
    db_conn.row_factory = sqlite3.Row
    return db_conn

def close_conn(db_conn):
    db_conn.close()

def init():
    if Path(JOBS_DB_FILE).is_file():
        logger.info("DB already initialized")
        return

    logger.info("Initializing DB")

    with open(JOBS_DB_SCHEMA) as f:
        db_conn = open_conn()
        with db_conn:
            db_conn.executescript(f.read())
        close_conn(db_conn)

def get_job(db_conn, job_key):
    with db_conn:
        c = db_conn.execute(
            '''
            SELECT * FROM jobs
            WHERE job_key = ?
            ''',
            (
                job_key,
            )
        )
        row = c.fetchone()

    if row:
        return {
            'job_key': row['job_key'],
            'thread_limit': row['thread_limit'],
            'target_email': row['target_email'],
            'time_filter': row['time_filter'],
            'cron_trigger': json.loads(row['cron_trigger']),
            'subreddit': row['subreddit'],
        }

def get_jobs(db_conn):
    rows = []
    with db_conn:
        c = db_conn.execute('SELECT * FROM jobs')
        rows = c.fetchall()

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

def insert_job(db_conn, data):
    job_key = get_new_job_key(db_conn)

    with db_conn:
        db_conn.execute(
            '''
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
            ''',
            (
                job_key,
                data['thread_limit'],
                data['target_email'],
                data['time_filter'],
                json.dumps(data['cron_trigger']),
                data['subreddit']
            )
        )

    return get_job(db_conn, job_key)

def update_job(db_conn, job_key, data):
    with db_conn:
        db_conn.execute(
            '''
            UPDATE jobs
            SET
                thread_limit = ?,
                target_email = ?,
                time_filter = ?,
                cron_trigger = ?,
                subreddit = ?
            WHERE
                job_key = ?
            ''',
            (
                data['thread_limit'],
                data['target_email'],
                data['time_filter'],
                json.dumps(data['cron_trigger']),
                data['subreddit'],
                job_key,
            )
        )

    return get_job(db_conn, job_key)

def delete_job(db_conn, job_key):
    with db_conn:
        db_conn.execute(
            'DELETE FROM jobs WHERE job_key = ?',
            (
                job_key,
            )
        )

def is_valid_job_key(db_conn, job_key):
    with db_conn:
        c = db_conn.execute(
            '''
            SELECT rowid FROM jobs WHERE job_key = ?
            ''',
            (
                job_key,
            )
        )
        row = c.fetchone()

    return row is not None

def get_new_job_key(db_conn):
    while True:
        random_key = ''.join(
            random.SystemRandom().choice(
                string.ascii_lowercase + string.ascii_uppercase + string.digits
            )
            for _ in range(JOB_KEY_LENGTH)
        )

        if not is_valid_job_key(db_conn, random_key):
            return random_key
