import unittest
from unittest.mock import patch

from rcollate import reddit

VALID_SUBREDDITS = ['test1', 'test2']
VALID_SUBREDDIT = VALID_SUBREDDITS[0]
INVALID_SUBREDDIT = 'test3'

class MockPrawNotFound(Exception):
    pass

class MockPrawSubreddit(object):
    def __init__(self, name, *args, **kwargs):
        self.display_name = ''
        self.permalink = ''
        self.selftext = ''
        self.title = ''
        self.ups = 0
        self.url = ''

    def top(*args, **kwargs):
        return []

class MockPrawSubreddits(object):
    def search_by_name(self, name, *args, **kwargs):
        if name in VALID_SUBREDDITS:
            return [
                MockPrawSubreddit(name)
            ]
        else:
            raise MockPrawNotFound()

class MockPraw(object):
    def subreddit(self, name, *args, **kwargs):
        return MockPrawSubreddit(name)

    @property
    def subreddits(self):
        return MockPrawSubreddits()

mock_praw = MockPraw()

class RedditTest(unittest.TestCase):
    def setUp(self):
        self.praw_patcher = patch('rcollate.reddit._reddit', mock_praw)
        self.praw_patcher.start()

    def tearDown(self):
        self.praw_patcher.stop()

    def test_top_subreddit_threads(self):
        r_threads = reddit.top_subreddit_threads('test', 'day', 10)

    def test_valid_subreddit_exists(self):
        self.assertTrue(reddit.subreddit_exists(VALID_SUBREDDIT))

    @patch('rcollate.reddit.NotFound', MockPrawNotFound)
    def test_invalid_subreddit_exists(self):
        self.assertFalse(reddit.subreddit_exists(INVALID_SUBREDDIT))

    def test_subreddit_search(self):
        reddit.subreddit_search(VALID_SUBREDDIT)
