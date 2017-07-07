from collections import namedtuple

import praw
from prawcore import NotFound

from rcollate.config import secrets, settings

Subreddit = namedtuple('Subreddit', [
    'display_name',
])

SubredditThread = namedtuple('SubredditThread', [
    'permalink',
    'selftext',
    'title',
    'ups',
    'url',
])

_reddit = praw.Reddit(
    client_id=secrets['client_id'],
    client_secret=secrets['client_secret'],
    user_agent=settings['user_agent']
)

def top_subreddit_threads(subreddit, time_filter, thread_limit):
    subreddit = _reddit.subreddit(subreddit)

    return (
        SubredditThread(
            permalink=r.permalink,
            selftext=r.selftext,
            title=r.title,
            ups=r.ups,
            url=r.url,
        )
        for r in subreddit.top(time_filter, limit=thread_limit)
    )

def subreddit_exists(subreddit):
    try:
        r = _reddit.subreddits.search_by_name(subreddit, exact=True)
        # Note: sometimes an empty results list is returned
        # without a NotFound exception being raised, so handle
        # that case by checking len.
        return len(r) > 0
    except NotFound:
        return False

def subreddit_search(subreddit):
    return [
        Subreddit(
            display_name=r.display_name,
        )
        for r in _reddit.subreddits.search_by_name(subreddit)
    ]
