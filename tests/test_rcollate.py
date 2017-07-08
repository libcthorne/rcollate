import unittest

import rcollate

class RCollateTestCase(unittest.TestCase):
    def setUp(self):
        rcollate.app.testing = True
        self.app = rcollate.app.test_client()

    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()
