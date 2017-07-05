from apscheduler.schedulers.background import BackgroundScheduler

from rcollate import logs
from rcollate.config import settings
from rcollate.mailer import Mailer
import rcollate.reddit as reddit

mailer = None
scheduler = None
job_schedules = None

get_job_by_job_key = None
get_job_url_by_job_key = None

logger = logs.get_logger()

def _run_job_by_job_key(job_key):
    run_job(get_job_by_job_key(job_key))

def run_job(job):
    mailer.send_threads(
        r_threads=reddit.top_subreddit_threads(
            job.subreddit,
            job.time_filter,
            job.thread_limit,
        ),
        target_email=job.target_email,
        subreddit=job.subreddit,
        job_view_url=get_job_url_by_job_key(job.job_key)
    )

def schedule_job(job):
    job_key = job.job_key
    job_schedules[job_key] = {
        '_handle': scheduler.add_job(
           _run_job_by_job_key, 'cron', [job_key], **job.cron_trigger
        )
    }

def unschedule_job(job):
    job_key = job.job_key
    job_schedule = job_schedules[job_key]
    job_schedule['_handle'].remove()
    del job_schedules[job_key]

def reschedule_job(job):
    job_key = job.job_key
    job_schedule = job_schedules[job_key]
    job_schedule['_handle'].reschedule('cron', **job.cron_trigger)

def start(
    initial_jobs,
    get_job_by_job_key_fn,
    get_job_url_by_job_key_fn,
):
    global mailer
    global scheduler
    global job_schedules

    global get_job_by_job_key
    global get_job_url_by_job_key

    mailer = Mailer(
        smtp_host=settings['smtp_host'],
        smtp_timeout=settings['smtp_timeout'],
        sender_name=settings['sender_name'],
        sender_email=settings['sender_email'],
    )

    scheduler = BackgroundScheduler()

    job_schedules = {}

    get_job_by_job_key = get_job_by_job_key_fn
    get_job_url_by_job_key = get_job_url_by_job_key_fn

    for job in initial_jobs:
        schedule_job(job)

    scheduler.start()
