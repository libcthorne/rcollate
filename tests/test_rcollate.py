import base64
import unittest
from unittest.mock import patch

from flask_socketio import SocketIO

import rcollate
from rcollate.reddit import Subreddit

DEFAULT_CRON_TRIGGER = {'hour': 7}
VALID_EMAIL_TIME = '7:00am'

VALID_SUBREDDITS = ['hello', 'world']
VALID_SUBREDDIT = VALID_SUBREDDITS[0]
INVALID_SUBREDDIT = 'test'

VALID_EMAIL = 'test@test.com'

def mock_subreddit_exists(subreddit):
    return subreddit in VALID_SUBREDDITS

class RCollateTestCase(unittest.TestCase):
    def setUp(self):
        rcollate.app.testing = True
        rcollate.app.config['WTF_CSRF_ENABLED'] = False
        self.app = rcollate.app.test_client()

        self.subreddit_exists_patcher = patch(
            'rcollate.reddit.subreddit_exists',
            mock_subreddit_exists
        )
        self.subreddit_exists_patcher.start()

    def tearDown(self):
        self.clear_jobs()

        self.subreddit_exists_patcher.stop()

    def create_job(self, subreddit=VALID_SUBREDDIT, target_email=VALID_EMAIL):
        with rcollate.app.app_context():
            job = rcollate.rcollate.create_job(subreddit, target_email, DEFAULT_CRON_TRIGGER)
        return job

    def clear_jobs(self):
        with rcollate.app.app_context():
            db_conn = rcollate.rcollate.get_db_conn()
            for job in rcollate.db.get_jobs(db_conn).values():
                rcollate.db.delete_job(db_conn, job.job_key)

    @property
    def auth_headers(self):
        return {
            'Authorization': 'Basic ' + base64.b64encode(
                b"test_user:test_password"
            ).decode('ascii')
        }

class JobsIndexPageTest(RCollateTestCase):
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
        job = self.create_job()
        rv = self.app.get('/jobs/', headers=self.auth_headers)
        self.assertIn('Job [' + job.job_key + ']', str(rv.data))

class JobsNewPageTest(RCollateTestCase):
    def test_get_status_code(self):
        rv = self.app.get('/jobs/new/')
        self.assertEqual(rv.status_code, 200)

    def test_post_invalid_subreddit(self):
        rv = self.app.post('/jobs/new/', data={
            'subreddit': INVALID_SUBREDDIT,
            'target_email': VALID_EMAIL,
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
            'target_email': VALID_EMAIL,
            'email_time': VALID_EMAIL_TIME,
        })
        self.assertEqual(rv.status_code, 302)
        self.assertRegex(rv.location, '/jobs/[0-9a-zA-Z]+')

class JobsShowPageTest(RCollateTestCase):
    def test_get_invalid_job(self):
        rv = self.app.get('/jobs/nonexistentjobkey/')
        self.assertEqual(rv.status_code, 404)
        self.assertIn('Job nonexistentjobkey not found', str(rv.data))

    def test_get_valid_job(self):
        job = self.create_job()
        rv = self.app.get('/jobs/%s/' % job.job_key)
        self.assertEqual(rv.status_code, 200)
        self.assertIn(job.job_key, str(rv.data))

class JobsDeletePageTest(RCollateTestCase):
    def test_delete_invalid_job(self):
        rv = self.app.post('/jobs/nonexistentjobkey/delete/')
        self.assertEqual(rv.status_code, 404)
        self.assertIn('Job nonexistentjobkey not found', str(rv.data))

    def test_delete_valid_job(self):
        job = self.create_job()
        rv = self.app.post('/jobs/%s/delete/' % job.job_key)
        self.assertEqual(rv.status_code, 302)

class JobsEditPageTest(RCollateTestCase):
    def test_get_invalid_job(self):
        rv = self.app.get('/jobs/nonexistentjobkey/edit/')
        self.assertEqual(rv.status_code, 404)
        self.assertIn('Job nonexistentjobkey not found', str(rv.data))

    def test_get_valid_job(self):
        job = self.create_job()
        rv = self.app.get('/jobs/%s/edit/' % job.job_key)
        self.assertEqual(rv.status_code, 200)

    def test_post_invalid_job(self):
        rv = self.app.post('/jobs/nonexistentjobkey/edit/')
        self.assertEqual(rv.status_code, 404)
        self.assertIn('Job nonexistentjobkey not found', str(rv.data))

    def test_post_valid_job_invalid_data(self):
        job = self.create_job()
        rv = self.app.post('/jobs/%s/edit/' % job.job_key, data={
            'subreddit': INVALID_SUBREDDIT,
        })
        self.assertEqual(rv.status_code, 400)

    def test_post_valid_job_valid_data(self):
        job = self.create_job()
        rv = self.app.post('/jobs/%s/edit/' % job.job_key, data={
            'subreddit': VALID_SUBREDDIT,
            'target_email': VALID_EMAIL,
            'email_time': VALID_EMAIL_TIME,
        })
        self.assertEqual(rv.status_code, 302)
        self.assertIn('/jobs/%s/' % job.job_key, rv.location)

class JobsRunPageTest(RCollateTestCase):
    def test_post_invalid_job(self):
        rv = self.app.post('/jobs/nonexistentjobkey/run/')
        self.assertEqual(rv.status_code, 404)
        self.assertIn('Job nonexistentjobkey not found', str(rv.data))

    @patch('rcollate.scheduler.mailer.send_threads')
    def test_post_valid_job(self, mock_send_threads):
        job = self.create_job()
        rv = self.app.post('/jobs/%s/run/' % job.job_key)
        self.assertEqual(rv.status_code, 302)
        self.assertIn('/jobs/%s/' % job.job_key, rv.location)

class SubredditSearchTest(RCollateTestCase):
    def mock_subreddit_search(subreddit):
        return [
            Subreddit('test1'),
            Subreddit('test2'),
        ]

    @patch('rcollate.reddit.subreddit_search', mock_subreddit_search)
    def test_search(self):
        client = rcollate.socketio.test_client(rcollate.app)
        client.emit('subreddit_search_request', {
            'subreddit': 'test',
        })
        received = client.get_received()
        print(received)
        client.disconnect()

class HelpersTest(RCollateTestCase):
    def test_get_job_by_job_key(self):
        job = self.create_job()
        self.assertEqual(
            rcollate.rcollate._get_job_by_job_key(job.job_key).job_id,
            job.job_id
        )
