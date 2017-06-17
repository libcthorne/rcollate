import logging

LOG_FILE_NAME = "rcollate.log"

logger = None

def get_logger():
    global logger

    if logger is not None:
        return logger

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Log line format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Console output handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Log file handler
    fh = logging.FileHandler(LOG_FILE_NAME)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
