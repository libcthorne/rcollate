CREATE TABLE jobs(
       job_key TEXT NOT NULL,
       thread_limit INTEGER NOT NULL,
       target_email TEXT NOT NULL,
       time_filter TEXT NOT NULL,
       cron_trigger BLOB NOT NULL,
       subreddit TEXT NOT NULL
)
