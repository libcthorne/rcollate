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

if __name__ == "__main__":
    unittest.main()
