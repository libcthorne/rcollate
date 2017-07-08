import base64
import unittest

import rcollate

class RCollateTestCase(unittest.TestCase):
    def setUp(self):
        rcollate.app.testing = True
        self.app = rcollate.app.test_client()

    def tearDown(self):
        pass

    @property
    def auth_headers(self):
        return {
            'Authorization': 'Basic ' + base64.b64encode(
                b"test_user:test_password"
            ).decode('ascii')
        }

class TestJobsIndex(RCollateTestCase):
    def test_jobs_index_no_auth(self):
        rv = self.app.get('/jobs/')
        self.assertEqual(rv.status_code, 401)

    def test_jobs_index_auth(self):
        rv = self.app.get('/jobs/', headers=self.auth_headers)
        self.assertEqual(rv.status_code, 200)

    def test_jobs_index_no_jobs(self):
        rv = self.app.get('/jobs/', headers=self.auth_headers)
        self.assertFalse('Job ' in str(rv.data))

    def test_jobs_index_with_jobs(self):
        with rcollate.app.app_context():
            job = rcollate.rcollate.create_job('_test_', '_test_')
            rv = self.app.get('/jobs/', headers=self.auth_headers)
            self.assertTrue('Job ' in str(rv.data))
            rcollate.rcollate.delete_job(job.job_key)

if __name__ == "__main__":
    unittest.main()
