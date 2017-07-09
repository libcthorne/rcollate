import os
import random
import string

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    MetaData,
    PickleType,
    String,
    Table,
)
from sqlalchemy.orm import mapper, sessionmaker

from rcollate import logs
from rcollate.config import settings
from rcollate.models import Job

JOBS_DB_FILE = 'db/jobs.db'
JOBS_DB_SCHEMA = 'db/jobs_schema.sql'
JOB_KEY_LENGTH = 20

os.makedirs(os.path.dirname(settings['db_file']), exist_ok=True)
engine = create_engine('sqlite:///{}'.format(settings['db_file']), echo=True)
metadata = MetaData()
Session = sessionmaker(bind=engine)

logger = logs.get_logger()

jobs_table = Table('jobs', metadata,
   Column('subreddit', String, nullable=False),
   Column('target_email', String, nullable=False),
   Column('cron_trigger', PickleType, nullable=False),
   Column('thread_limit', Integer, nullable=False),
   Column('time_filter', String, nullable=False),
   Column('job_id', Integer, primary_key=True),
   Column('job_key', String, nullable=False),
)
mapper(Job, jobs_table)

def open_conn():
    return Session()

def close_conn(db_conn):
    db_conn.close()

def init():
    metadata.create_all(bind=engine)

def get_job(db_conn, job_key):
    job = db_conn.query(Job).filter_by(job_key=job_key).one()
    return job

def get_jobs(db_conn):
    jobs = db_conn.query(Job).all()
    return {
        job.job_key: job for job in jobs
    }

def insert_job(db_conn, job):
    if job.job_key is None:
        job.job_key = get_new_job_key(db_conn)

    db_conn.add(job)
    db_conn.commit()

    return job

def update_job(db_conn, job):
    db_conn.commit()
    return job

def delete_job(db_conn, job_key):
    job = db_conn.query(Job).filter_by(job_key=job_key).one()
    db_conn.delete(job)
    db_conn.commit()

def is_valid_job_key(db_conn, job_key):
    return db_conn.query(Job.job_id).\
        filter_by(job_key=job_key).count() == 1

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
