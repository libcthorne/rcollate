import praw
from prawcore import NotFound

from rcollate.config import secrets, settings

_reddit = praw.Reddit(
    client_id=secrets["client_id"],
    client_secret=secrets["client_secret"],
    user_agent=settings["user_agent"]
)

def top_subreddit_threads(subreddit, time_filter, thread_limit):
    subreddit = _reddit.subreddit(subreddit)

    return subreddit.top(time_filter, limit=thread_limit)

def subreddit_exists(subreddit):
    try:
        r = _reddit.subreddits.search_by_name(subreddit, exact=True)
        # Note: sometimes an empty results list is returned
        # without a NotFound exception being raised, so handle
        # that case by checking len.
        return len(r) > 0
    except NotFound:
        return False
