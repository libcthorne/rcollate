import json
import sys

from rcollate import logs

logger = logs.get_logger()

def read_json_file(file_name, required=True, default=None):
    try:
        with open(file_name) as f:
            return json.load(f)
    except IOError:
        if required:
            logger.error("%s missing", file_name)
            sys.exit(1)
        else:
            return default
