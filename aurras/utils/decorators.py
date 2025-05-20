"""Decorators for error handling and logging."""

from functools import wraps

from aurras.utils.logger import get_logger

# logging.basicConfig(filename=_path_manager.log_file, level=logging.ERROR)
logger = get_logger("aurras.utils.decorators", log_to_console=False)


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
            logger.error("Exception in %s : %s", func.__name__, e)

            return "An unexpected error occurred. Please check the logs for details."

    return wrapper


def with_error_handling(method):
    """Decorator to standardize error handling in processor methods."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)

        except Exception as e:
            from aurras.utils.console import console

            method_name = method.__name__

            console.print_error(f"Error in {method_name}: {str(e)}")
            logger.error(f"Error in {method_name}: {e}", exc_info=True)
            return 1

    return wrapper
