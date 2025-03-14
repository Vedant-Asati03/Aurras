from functools import wraps
from pathlib import Path
import logging

# Fix the import to use relative paths
from ..utils.path_manager import PathManager

# Create a pathmanager instance
_path_manager = PathManager()
dir = Path.home() / ".aurras"

dir.mkdir(parents=True, exist_ok=True)

# Set up logging
logging.basicConfig(filename=_path_manager.log_file, level=logging.ERROR)


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
