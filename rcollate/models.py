from datetime import datetime

class Job(object):
    def __init__(
        self,
        subreddit,
        target_email,
        cron_trigger,
        thread_limit=10,
        time_filter='day',
        job_id=None,
        job_key=None,
    ):
        self.subreddit = subreddit
        self.target_email = target_email
        self.cron_trigger = cron_trigger
        self.thread_limit = thread_limit
        self.time_filter = time_filter
        self.job_id = job_id
        self.job_key = job_key

    @property
    def cron_trigger_datetime(self):
        return datetime.strptime(
            '{}:{}'.format(
                self.cron_trigger['hour'],
                self.cron_trigger.get('minute', 0),
            ),
            '%H:%M'
        )

    @property
    def cron_trigger_str(self):
        return self.cron_trigger_datetime.strftime(
            '%I:%M%p'
        )

    def __repr__(self):
        return "<Job(job_key=%s, subreddit=%s)>" % (
            self.job_key,
            self.subreddit,
        )
