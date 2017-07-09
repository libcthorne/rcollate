import unittest

from rcollate.mailer import Mailer

class MailerTest(unittest.TestCase):
    def test_valid_send(self):
        mailer = Mailer(
            smtp_host='localhost',
            smtp_timeout=5,
            sender_name='TEST',
            sender_email='test@test.com',
        )

        success = mailer.send_threads(
            r_threads=[],
            target_email='test2@test.com',
            subreddit='test',
            job_view_url='test',
        )

        self.assertTrue(success)

    def test_invalid_send(self):
        mailer = Mailer(
            smtp_host='INVALIDHOST[]~',
            smtp_timeout=5,
            sender_name='TEST',
            sender_email='test@test.com',
        )

        success = mailer.send_threads(
            r_threads=[],
            target_email='test2@test.com',
            subreddit='test',
            job_view_url='test',
        )

        self.assertFalse(success)
