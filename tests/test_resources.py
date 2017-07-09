import unittest

from rcollate import resources

INVALID_PATH = 'INVALID:PATH~|[]'

class ResourcesTest(unittest.TestCase):
    def test_invalid_required_resource(self):
        with self.assertRaises(SystemExit):
            resources.read_json_file(
                INVALID_PATH, required=True
            )

    def test_invalid_optional_resource(self):
        self.assertEqual(
            resources.read_json_file(
                INVALID_PATH, required=False, default='TEST',
            ),
            'TEST'
        )
