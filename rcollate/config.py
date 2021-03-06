import json
import os
import sys

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from rcollate import resources

SETTINGS_SCHEMA = {
    'type': 'object',
    'properties': {
        'user_agent': {'type': 'string'},
        'sender_name': {'type': 'string'},
        'sender_email': {'type': 'string'},
        'smtp_host': {'type': 'string'},
        'smtp_timeout': {'type': 'integer'},
        'app_url': {'type': 'string'},
        'db_file': {'type': 'string'},
    },
    'required': [
        'user_agent',
        'sender_name',
        'sender_email',
        'smtp_host',
        'smtp_timeout',
        'app_url',
        'db_file',
    ],
    'additionalProperties': False,
}

SECRETS_SCHEMA = {
    'type': 'object',
    'properties': {
        'client_id': {'type': 'string'},
        'client_secret': {'type': 'string'},
        'admin_username': {'type': 'string'},
        'admin_password': {'type': 'string'},
        'session_secret_key': {'type': 'string'},
    },
    'required': [
        'client_id',
        'client_secret',
        'admin_username',
        'admin_password',
        'session_secret_key',
    ],
    'additionalProperties': False,
}

def read_config_file(path, schema):
    contents = resources.read_json_file(path)

    try:
        validate(contents, schema)
        return contents
    except ValidationError as e:
        print("Error reading {}: {}".format(
            path,
            e.message,
        ))
        sys.exit(1)

config_dir = os.environ.get('CONFIG_DIR', 'config')

settings = read_config_file(
    '{}/settings.json'.format(config_dir),
    SETTINGS_SCHEMA
)

secrets = read_config_file(
    '{}/secrets.json'.format(config_dir),
    SECRETS_SCHEMA
)
