import unittest

from rcollate import models

class ModelsTest(unittest.TestCase):
    def test_job_model_create_no_key(self):
        job = models.Job(
            subreddit='hello',
            target_email='test@test.com',
            cron_trigger={'hour': 6},
        )

        self.assertEqual(
            str(job),
            '<Job(job_key=None, subreddit=hello)>'
        )
