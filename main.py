import logging

from pytools.logging import setup_logging

setup_logging(log_to_file=True, log_level=logging.INFO)

logging.info(msg="This is an info message.")
logging.warning(msg="This is a warning message")
logging.error(msg="This is an error message")
