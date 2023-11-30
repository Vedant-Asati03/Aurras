from functools import wraps
import logging

import config.config as path


# Set up logging
logging.basicConfig(filename=path.aurras_log, level=logging.ERROR)


def handle_exceptions(func):
    """
    A decorator to catch unhandled exceptions and log them.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the exception
            logging.error("Exception in %s : %s", func.__name__, e)

            return "An unexpected error occurred. Please check the logs for details."

    return wrapper
