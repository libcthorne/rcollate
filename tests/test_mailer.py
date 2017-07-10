import unittest
from unittest.mock import patch

from rcollate.mailer import Mailer

class ResponseMock(object):
    def __init__(self, status_code):
        self.status_code = status_code
        self.error = status_code

class MessageMock(object):
    def __init__(self, *_args, **_kwargs):
        pass

class ValidMessageMock(MessageMock):
    def send(self, *args, **kwargs):
        return ResponseMock(250)

class InvalidMessageMock(MessageMock):
    def send(self, *args, **kwargs):
        return ResponseMock(0)

class MailerTest(unittest.TestCase):
    def setUp(self):
        self.mailer = Mailer(
            smtp_host='localhost',
            smtp_timeout=5,
            sender_name='TEST',
            sender_email='test@test.com',
        )

    @patch('rcollate.mailer.emails.html', ValidMessageMock)
    def test_valid_send(self):
        success = self.mailer.send_threads(
            r_threads=[],
            target_email='test2@test.com',
            subreddit='test',
            job_view_url='test',
        )

        self.assertTrue(success)

    @patch('rcollate.mailer.emails.html', InvalidMessageMock)
    def test_invalid_send(self):
        success = self.mailer.send_threads(
            r_threads=[],
            target_email='test2@test.com',
            subreddit='test',
            job_view_url='test',
        )

        self.assertFalse(success)
