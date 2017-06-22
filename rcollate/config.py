import json

from rcollate import resources

settings = resources.read_json_file("config/settings.json")
secrets = resources.read_json_file("config/secrets.json")
