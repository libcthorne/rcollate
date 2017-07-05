import random
import string

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    PickleType,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from rcollate import logs

JOBS_DB_FILE = 'db/jobs.db'
JOBS_DB_SCHEMA = 'db/jobs_schema.sql'
JOB_KEY_LENGTH = 20

engine = create_engine('sqlite:///{}'.format(JOBS_DB_FILE), echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

logger = logs.get_logger()

class Job(Base):
    __tablename__ = 'jobs'

    job_id = Column(Integer, primary_key=True)
    job_key = Column(String, nullable=False)
    thread_limit = Column(Integer, nullable=False)
    target_email = Column(String, nullable=False)
    time_filter = Column(String, nullable=False)
    cron_trigger = Column(PickleType, nullable=False)
    subreddit = Column(String, nullable=False)

    def __repr__(self):
        return "<Job(job_key=%s, subreddit=%s)>" % (
            self.job_key,
            self.subreddit,
        )

def open_conn():
    return Session()

def close_conn(db_conn):
    db_conn.close()

def init():
    Base.metadata.create_all(engine)

def get_job(db_conn, job_key):
    job = db_conn.query(Job).filter_by(job_key=job_key).one()
    return job

def get_jobs(db_conn):
    jobs = db_conn.query(Job).all()
    return {
        job.job_key: job for job in jobs
    }

def insert_job(db_conn, data):
    job_key = get_new_job_key(db_conn)
    job = Job(
        job_key=job_key,
        thread_limit=data['thread_limit'],
        target_email=data['target_email'],
        time_filter=data['time_filter'],
        cron_trigger=data['cron_trigger'],
        subreddit=data['subreddit'],
    )

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
