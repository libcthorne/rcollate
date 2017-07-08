import base64
import unittest

import rcollate

VALID_SUBREDDITS = ['hello', 'world']
VALID_SUBREDDIT = VALID_SUBREDDITS[0]
INVALID_SUBREDDIT = 'test'

def mock_subreddit_exists(subreddit):
    return subreddit in VALID_SUBREDDITS

class RCollateTestCase(unittest.TestCase):
    def setUp(self):
        rcollate.app.testing = True
        rcollate.app.config['WTF_CSRF_ENABLED'] = False
        self.app = rcollate.app.test_client()

        self.mocks = {}
        self.mocks['subreddit_exists'] = rcollate.reddit.subreddit_exists
        rcollate.reddit.subreddit_exists = mock_subreddit_exists

    def tearDown(self):
        rcollate.reddit.subreddit_exists = self.mocks['subreddit_exists']

    @property
    def auth_headers(self):
        return {
            'Authorization': 'Basic ' + base64.b64encode(
                b"test_user:test_password"
            ).decode('ascii')
        }

class TestJobsIndexPage(RCollateTestCase):
    def test_no_auth(self):
        rv = self.app.get('/jobs/')
        self.assertEqual(rv.status_code, 401)

    def test_auth(self):
        rv = self.app.get('/jobs/', headers=self.auth_headers)
        self.assertEqual(rv.status_code, 200)

    def test_no_jobs(self):
        rv = self.app.get('/jobs/', headers=self.auth_headers)
        self.assertFalse('Job ' in str(rv.data))

    def test_with_jobs(self):
        with rcollate.app.app_context():
            job = rcollate.rcollate.create_job('_test_', '_test_')
            rv = self.app.get('/jobs/', headers=self.auth_headers)
            self.assertTrue('Job ' in str(rv.data))
            rcollate.rcollate.delete_job(job.job_key)

class TestJobsNewPage(RCollateTestCase):
    def test_get_status_code(self):
        rv = self.app.get('/jobs/new/')
        self.assertEqual(rv.status_code, 200)

    def test_post_invalid_subreddit(self):
        rv = self.app.post('/jobs/new/', data={
            'subreddit': INVALID_SUBREDDIT,
            'target_email': 'test@test.com',
        })
        self.assertTrue('Please enter a valid subreddit' in str(rv.data))

    def test_post_invalid_email(self):
        rv = self.app.post('/jobs/new/', data={
            'subreddit': VALID_SUBREDDIT,
            'target_email': 'test',
        })
        self.assertTrue('Please enter a valid email' in str(rv.data))

    def test_post_valid(self):
        rv = self.app.post('/jobs/new/', data={
            'subreddit': VALID_SUBREDDIT,
            'target_email': 'test@test.com',
        })
        self.assertEqual(rv.status_code, 302)
        self.assertRegex(rv.location, '/jobs/[0-9a-zA-Z]+')


if __name__ == "__main__":
    unittest.main()
