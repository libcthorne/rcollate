import unittest

from rcollate import config

class ConfigTest(unittest.TestCase):
    def test_invalid_config(self):
        with self.assertRaises(SystemExit):
            config.read_config_file(
                'config/tests_config/settings_invalid.json',
                config.SETTINGS_SCHEMA
            )
