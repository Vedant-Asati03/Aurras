"""
Aurras Logger Module

This module provides a centralized logging configuration for the Aurras music player.
It sets up loggers with appropriate handlers and formatters for different logging needs.
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import date
from typing import Dict, Optional, Union, List

from aurras.utils.path_manager import _path_manager

DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_ROTATION = "midnight"  # Can be 'midnight', 'W0'-'W6', or a number of bytes
LOG_BACKUP_COUNT = 14  # Keep 14 days of logs by default

_loggers: Dict[str, logging.Logger] = {}
_handlers: Dict[str, logging.Handler] = {}


def get_logfile_path(name: Optional[str] = None) -> Path:
    """
    Returns path to the log file for today or a specific component.

    Args:
        name: Optional component name for separate log files

    Returns:
        Path: The path to the log file
    """
    today = date.today().strftime("%Y-%m-%d")

    if name:
        filename = f"{today}_{name}.log"
    else:
        filename = f"{today}.log"

    return _path_manager.log_dir / filename


def setup_logger(
    name: str = "aurras",
    level: Union[int, str] = DEFAULT_LOG_LEVEL,
    log_to_console: bool = True,
    log_to_file: bool = True,
    propagate: bool = False,
    filename: Optional[str] = None,
    log_format: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
) -> logging.Logger:
    """
    Set up a logger with the given name and configuration.

    Args:
        name: Name of the logger
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
        propagate: Whether to propagate to parent loggers
        filename: Optional specific filename for the log file
        log_format: Format string for the log messages
        date_format: Format string for the timestamps

    Returns:
        logging.Logger: Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)

    # Convert string level to numeric if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), DEFAULT_LOG_LEVEL)

    logger.setLevel(level)
    logger.propagate = propagate

    formatter = logging.Formatter(log_format, date_format)

    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        _handlers[f"{name}_console"] = console_handler

    if log_to_file:
        if not filename:
            log_file = get_logfile_path(name)
        else:
            log_file = _path_manager.log_dir / filename

        # Use TimedRotatingFileHandler to rotate logs daily
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file, when=LOG_ROTATION, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        _handlers[f"{name}_file"] = file_handler

    # Store the logger for reuse
    _loggers[name] = logger

    return logger


def get_logger(
    name: str = "aurras", log_to_console: Optional[bool] = None
) -> logging.Logger:
    """
    Get a logger by name. If it doesn't exist, create it with default settings.

    Args:
        name: Name of the logger
        log_to_console: Whether to log to console, overriding the global setting
                       (None = use global setting)

    Returns:
        logging.Logger: The requested logger
    """
    if name in _loggers:
        return _loggers[name]

    # If log_to_console not specified, use the global setting
    console_output = (
        log_to_console
        if log_to_console is not None
        else (CONSOLE_LOGGING or DEBUG_MODE)
    )

    return setup_logger(name, log_to_console=console_output)


def update_log_level(name: str, level: Union[int, str]) -> None:
    """
    Update the log level for an existing logger.

    Args:
        name: Name of the logger
        level: New logging level
    """
    if name in _loggers:
        # Convert string level to numeric if needed
        if isinstance(level, str):
            level = getattr(logging, level.upper(), DEFAULT_LOG_LEVEL)

        _loggers[name].setLevel(level)


def enable_debug_for_all() -> None:
    """Enable debug logging for all loggers."""
    for logger in _loggers.values():
        logger.setLevel(logging.DEBUG)


def disable_debug_for_all() -> None:
    """Disable debug logging for all loggers (set to INFO)."""
    for logger in _loggers.values():
        logger.setLevel(logging.INFO)


def get_all_loggers() -> List[str]:
    """
    Get a list of all registered logger names.

    Returns:
        List[str]: Names of all registered loggers
    """
    return list(_loggers.keys())


# Determine if we should log to console based on environment variables
# Only log to console if explicitly requested or in debug mode
CONSOLE_LOGGING = os.environ.get("AURRAS_CONSOLE_LOGGING", "").lower() in (
    "true",
    "yes",
    "1",
)
DEBUG_MODE = os.environ.get("AURRAS_DEBUG", "").lower() in ("true", "yes", "1")
log_to_console = CONSOLE_LOGGING or DEBUG_MODE

# Configure the root logger
root_logger = setup_logger(
    name="aurras",
    level=os.environ.get("AURRAS_LOG_LEVEL", "INFO"),
    log_to_console=log_to_console,
    log_to_file=True,
)

# Create some common loggers with appropriate levels
player_logger = setup_logger("aurras.player", "INFO", log_to_console=log_to_console)
ui_logger = setup_logger("aurras.ui", "INFO", log_to_console=log_to_console)
core_logger = setup_logger("aurras.core", "INFO", log_to_console=log_to_console)
services_logger = setup_logger("aurras.services", "INFO", log_to_console=log_to_console)
themes_logger = setup_logger("aurras.themes", "INFO", log_to_console=log_to_console)
command_logger = setup_logger("aurras.command", "INFO", log_to_console=log_to_console)


# For backward compatibility
def debug_log(message: str) -> None:
    """
    Log a debug message using the root logger.

    Args:
        message: The message to log
    """
    root_logger.debug(message)


def exception_log(message: str, exc_info=True) -> None:
    """
    Log an exception message using the root logger.

    Args:
        message: The message to log
        exc_info: Whether to include exception info
    """
    root_logger.exception(message, exc_info=exc_info)


def info_log(message: str) -> None:
    """
    Log an info message using the root logger.

    Args:
        message: The message to log
    """
    root_logger.info(message)


def warning_log(message: str) -> None:
    """
    Log a warning message using the root logger.

    Args:
        message: The message to log
    """
    root_logger.warning(message)


def error_log(message: str) -> None:
    """
    Log an error message using the root logger.

    Args:
        message: The message to log
    """
    root_logger.error(message)


# Entry point for testing the logger
if __name__ == "__main__":
    print(f"Log directory: {_path_manager.log_dir}")
    print(f"Default log file: {get_logfile_path()}")

    # Test logging
    debug_log("This is a debug test message")
    info_log("This is an info test message")
    warning_log("This is a warning test message")
    error_log("This is an error test message")

    try:
        raise ValueError("This is a test exception")
    except Exception as e:
        exception_log(f"Caught an exception: {e}")

    print("Log test complete. Check the logs directory for the output.")
