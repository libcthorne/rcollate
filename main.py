import emails
import json
import praw
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from jinja2 import Template

HTML_EMAIL_TEMPLATE = Template("""
    {% for r_thread in r_threads %}
      {{ loop.index }}. {{ r_thread.title }} ({{ r_thread.ups }} upvotes)
      <br/>
      <a href='{{ r_thread.url }}'>{{ r_thread.url }}</a>
      <br/>
      <a href='https://www.reddit.com{{ r_thread.permalink }}'>{{ r_thread.permalink }}</a>

      {% if r_thread.selftext %}
        <p>{{ r_thread.selftext }}</p>
      {% endif %}

      <hr/>
    {% endfor %}
""")

settings = None
secrets = None
jobs = None

def load_config_files():
    global settings
    global secrets
    global jobs

    try:
        with open('settings.json') as f:
            settings = json.load(f)
    except IOError:
        print("settings.json missing")
        sys.exit(1)

    try:
        with open('secrets.json') as f:
            secrets = json.load(f)
    except IOError:
        print("secrets.json missing (see example_secrets.json for a template)")
        sys.exit(1)

    try:
        with open('jobs.json') as f:
            jobs = json.load(f)
    except IOError:
        print("jobs.json missing (see example_jobs.json for a template)")
        sys.exit(1)

def send_email(job):
    print("Send /r/{} email to {}".format(job["subreddit"], job["target_email"]))

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
        print("Sent /r/{} email to {}".format(
            job["subreddit"], job["target_email"]
        ))
    else:
        print("Error sending /r/{} email to {}: status_code={}, err={}".format(
            job["subreddit"], job["target_email"], r.status_code, r.error
        ))

def run():
    load_config_files()

    scheduler = BlockingScheduler()

    for job in jobs:
        scheduler.add_job(send_email, 'cron', [job], **job["cron_trigger"])

    scheduler.start()

if __name__ == "__main__":
    run()
