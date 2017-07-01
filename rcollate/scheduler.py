from apscheduler.schedulers.background import BackgroundScheduler

from rcollate import logs
from rcollate.config import settings
from rcollate.mailer import Mailer
import rcollate.db as db
import rcollate.reddit as reddit

mailer = None
scheduler = None
job_schedules = None

logger = logs.get_logger()

def run_job(job_key):
    job = db.get_job(job_key)

    mailer.send_threads(
        r_threads=reddit.top_subreddit_threads(
            job['subreddit'],
            job['time_filter'],
            job['thread_limit'],
        ),
        target_email=job['target_email'],
        subreddit=job['subreddit'],
        job_view_url=get_full_job_view_url(job['job_key'])
    )

def schedule_job(job_key):
    job = db.get_job(job_key)
    job_schedules[job_key] = {
        '_handle': scheduler.add_job(
           run_job, 'cron', [job_key], **job['cron_trigger']
        )
    }

def unschedule_job(job_key):
    job_schedule = job_schedules[job_key]
    job_schedule['_handle'].remove()
    del job_schedules[job_key]

def reschedule_job(job_key):
    job = db.get_job(job_key)
    job_schedule = job_schedules[job_key]
    job_schedule['_handle'].reschedule('cron', **job['cron_trigger'])

def init(get_full_job_view_url_fn):
    global get_full_job_view_url
    get_full_job_view_url = get_full_job_view_url_fn

def start():
    global mailer
    global scheduler
    global job_schedules

    mailer = Mailer(
        smtp_host=settings['smtp_host'],
        smtp_timeout=settings['smtp_timeout'],
        sender_name=settings['sender_name'],
        sender_email=settings['sender_email'],
    )

    scheduler = BackgroundScheduler()

    job_schedules = {
        job_key: {
            '_handle': scheduler.add_job(
               run_job, 'cron', [job_key], **job['cron_trigger']
            )
        }
        for job_key, job in db.get_jobs().items()
    }

    scheduler.start()
