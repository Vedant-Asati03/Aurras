"""
Enhanced Logging System for Aurras - Version 2

This module provides a robust, structured logging system with:
- JSON-first structured logging
- Performance profiling integration
- Theme-aware console output
- Context managers and decorators
- Debug mode control
- Standard Python logging interface
"""

import os
import json
import time
import psutil
import logging
import traceback
import threading
import logging.handlers
from pathlib import Path
from functools import wraps
from rich.console import Console
from contextlib import contextmanager
from typing import Any, Dict, Optional, Callable

from aurras.utils.path_manager import _path_manager


class LoggerConfig:
    """Thread-safe configuration manager for the logging system."""

    def __init__(self):
        self._lock = threading.Lock()
        self._debug_mode = False
        self._suppress_levels = []
        self._console = None

        self.SLOW_OPERATION_THRESHOLD_MS = 1000
        self.MEMORY_UNIT_MB = 1024 * 1024
        self.LOG_FILE_MAX_SIZE = 10 * self.MEMORY_UNIT_MB
        self.LOG_FILE_BACKUP_COUNT = 5

        self.LEVEL_COLORS = {
            "debug": "#6272A4",
            "info": "#8BE9FD",
            "warning": "#FFB86C",
            "error": "#FF5555",
            "critical": "#FF0000",
        }

    @property
    def debug_mode(self) -> bool:
        """Get debug mode status."""
        with self._lock:
            return self._debug_mode

    @debug_mode.setter
    def debug_mode(self, enabled: bool):
        """Set debug mode status."""
        with self._lock:
            self._debug_mode = enabled

    @property
    def suppress_levels(self) -> list:
        """Get suppressed log levels."""
        with self._lock:
            return self._suppress_levels.copy()

    def set_suppress_levels(self, levels: Optional[str] = None):
        """Set log levels to suppress from console output."""
        with self._lock:
            if levels == "all":
                self._suppress_levels = ["debug", "info"]
            elif levels:
                self._suppress_levels = [levels] if isinstance(levels, str) else levels
            else:
                self._suppress_levels = []

    def get_console(self) -> Console:
        """Get cached console instance with thread-safe lazy initialization."""
        if self._console is None:
            with self._lock:
                if self._console is None:  # Double-check locking pattern
                    self._console = Console()
        return self._console

    def reset(self):
        """Reset configuration to defaults (useful for testing)."""
        with self._lock:
            self._debug_mode = False
            self._suppress_levels = []
            self._console = None


_config = LoggerConfig()


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    __slots__ = ("_json_separators",)

    def __init__(self):
        super().__init__()
        # Cache separators for performance
        self._json_separators = (",", ":")

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_data, separators=self._json_separators)


class DebugConsoleHandler(logging.Handler):
    """Custom console handler for debug mode with theme-aware output."""

    __slots__ = ("_level_colors", "_time_format")

    def __init__(self):
        super().__init__()
        self.setLevel(logging.DEBUG)
        self._time_format = "%H:%M:%S"

    def emit(self, record: logging.LogRecord):
        """Emit log record to console with theme colors."""
        if not _config.debug_mode:
            return

        log_level = record.levelname.lower()
        if log_level in _config.suppress_levels:
            return

        color = _config.LEVEL_COLORS.get(log_level, _config.LEVEL_COLORS["info"])
        timestamp = time.strftime(self._time_format)

        # Build message more efficiently
        message_parts = [
            f"[{timestamp}] [bold]{record.levelname}[/bold]",
            f"[italic]{record.name}[/italic]",
            record.getMessage(),
        ]

        if hasattr(record, "extra_data") and record.extra_data:
            extras = []
            for key, value in record.extra_data.items():
                if isinstance(value, (list, dict)):
                    extras.append(f"{key}={str(value)}")
                else:
                    extras.append(f"{key}={value}")

            if extras:  # Start tracking
                message_parts.append(f"| {' | '.join(extras)}")

        message = " · ".join(message_parts)
        _config.get_console().print(message, style=color)


class LazyFileHandler(logging.Handler):
    """File handler that only creates log files when there's content to log."""

    __slots__ = ("log_file_path", "file_handler", "_formatter")

    def __init__(self, log_file_path: Path):
        super().__init__()
        self.log_file_path = log_file_path
        self.file_handler = None
        self._formatter = JSONFormatter()
        self.setFormatter(self._formatter)
        self.setLevel(logging.DEBUG)

    def emit(self, record):
        """Emit log record, creating file handler lazily."""
        if self.file_handler is None:
            self._initialize_file_handler()

        # Delegate to the actual file handler
        self.file_handler.emit(record)

    def _initialize_file_handler(self):
        """Initialize the file handler lazily."""
        # Create directory if it doesn't exist
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create the actual file handler
        self.file_handler = logging.handlers.RotatingFileHandler(
            self.log_file_path,
            maxBytes=_config.LOG_FILE_MAX_SIZE,
            backupCount=_config.LOG_FILE_BACKUP_COUNT,
        )
        self.file_handler.setFormatter(self._formatter)
        self.file_handler.setLevel(self.level)

    def close(self):
        """Close the file handler if it exists."""
        if self.file_handler:
            self.file_handler.close()
        super().close()


class PerformanceTracker:
    """Tracks performance metrics for logging."""

    __slots__ = ("start_time", "start_memory", "operation", "_process")

    def __init__(self):
        self.start_time: float = 0
        self.start_memory: float = 0
        self.operation: str = ""
        self._process = None

    def start(self, operation: str):
        """Start tracking an operation."""
        if not operation:
            raise ValueError("Operation name cannot be empty")

        self.operation = operation
        self.start_time = time.time()
        self.start_memory = self._get_memory_usage()

    def end(self) -> Dict[str, Any]:
        """End tracking and return metrics."""
        end_time = time.time()
        duration_ms = (end_time - self.start_time) * 1000
        end_memory = self._get_memory_usage()

        return {
            "operation": self.operation,
            "duration_ms": round(duration_ms, 2),
            "memory_before_mb": round(self.start_memory, 2),
            "memory_after_mb": round(end_memory, 2),
            "memory_delta_mb": round(end_memory - self.start_memory, 2),
        }

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            if self._process is None:
                self._process = psutil.Process(os.getpid())
            return self._process.memory_info().rss / _config.MEMORY_UNIT_MB
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
            return 0.0


class EnhancedLogger:
    """Enhanced logger with context management and performance tracking."""

    __slots__ = (
        "name",
        "logger",
        "_context",
        "_performance_tracker",
        "_handlers_setup",
    )

    def __init__(self, name: str):
        if not name:
            raise ValueError("Logger name cannot be empty")

        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Thread-local storage for context
        self._context = threading.local()

        # Performance tracking (lazy initialization)
        self._performance_tracker = None
        self._handlers_setup = False

        # Setup handlers if not already configured
        if not self.logger.handlers:
            self._setup_handlers()

    def _get_performance_tracker(self) -> PerformanceTracker:
        """Get performance tracker, creating it lazily."""
        if self._performance_tracker is None:
            self._performance_tracker = PerformanceTracker()
        return self._performance_tracker

    def _setup_handlers(self):
        """Setup file and console handlers."""
        if self._handlers_setup:
            return

        console_handler = DebugConsoleHandler()
        self.logger.addHandler(console_handler)

        # Use lazy file handler - only creates file when needed
        log_file = _path_manager.log_dir / f"{self.name.replace('.', '_')}.log"
        file_handler = LazyFileHandler(log_file)
        self.logger.addHandler(file_handler)

        self._handlers_setup = True

    def _get_context(self) -> Dict[str, Any]:
        """Get current thread-local context."""
        if not hasattr(self._context, "data"):
            self._context.data = {}
        return self._context.data

    def _log_with_context(
        self, level: int, message: str, extra: Optional[Dict[str, Any]] = None
    ):
        """Log message with context and extra data."""
        # Merge context with extra data (optimize for common case)
        context_data = self._get_context()
        if extra:
            if context_data:
                log_data = context_data.copy()
                log_data.update(extra)
            else:
                log_data = extra
        else:
            log_data = context_data

        # Create log record with extra data
        record = self.logger.makeRecord(self.name, level, "", 0, message, (), None)
        record.extra_data = log_data

        # Handle the record
        self.logger.handle(record)

    # Standard logging methods
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, extra)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log_with_context(logging.INFO, message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, extra)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self._log_with_context(logging.ERROR, message, extra)

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, extra)

    # Context management methods
    @contextmanager
    def operation_context(self, **context):
        """Context manager for adding operation context to logs."""
        old_context = self._get_context().copy()
        self._get_context().update(context)
        try:
            yield
        finally:
            self._context.data = old_context

    @contextmanager
    def profile_context(self, operation: str, monitor_resources: bool = False):
        """Context manager for performance profiling."""
        if not operation:
            raise ValueError("Operation name cannot be empty")

        tracker = self._get_performance_tracker()
        tracker.start(operation)

        with self.operation_context(operation=operation):
            try:
                yield
            finally:
                metrics = tracker.end()

                if metrics["duration_ms"] > _config.SLOW_OPERATION_THRESHOLD_MS:
                    self.warning("Slow operation detected", extra=metrics)
                else:
                    self.info("Operation completed", extra=metrics)

    def profile_operation(self, operation: str, slow_threshold_ms: int = None):
        """Decorator for profiling function operations."""
        if not operation:
            raise ValueError("Operation name cannot be empty")

        if slow_threshold_ms is None:
            slow_threshold_ms = _config.SLOW_OPERATION_THRESHOLD_MS

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.profile_context(operation):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    # System monitoring methods
    def memory_checkpoint(self, checkpoint_name: str):
        """Log current memory usage as checkpoint."""
        if not checkpoint_name:
            raise ValueError("Checkpoint name cannot be empty")

        try:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / _config.MEMORY_UNIT_MB
            self.info(
                "Memory checkpoint",
                extra={
                    "checkpoint": checkpoint_name,
                    "memory_mb": round(memory_mb, 2),
                },
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError) as e:
            self.debug(f"Memory checkpoint failed: {e}")

    def system_metrics(self):
        """Log current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage("/").percent

            self.info(
                "System metrics",
                extra={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_usage_percent": disk_percent,
                },
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError) as e:
            self.debug(f"System metrics failed: {e}")

    def performance_summary(
        self, summary_type: str, extra: Optional[Dict[str, Any]] = None
    ):
        """Log performance summary."""
        if not summary_type:
            raise ValueError("Summary type cannot be empty")

        summary_data = {"summary_type": summary_type}
        if extra:
            summary_data.update(extra)
        self.info("Performance summary", extra=summary_data)


_loggers: Dict[str, EnhancedLogger] = {}
_logger_lock = threading.Lock()


def set_debug_mode(enabled: bool):
    """Enable or disable debug mode globally."""
    _config.debug_mode = enabled


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return _config.debug_mode


def set_suppress_levels(levels: Optional[str] = None):
    """Set log levels to suppress from console output."""
    _config.set_suppress_levels(levels)


def get_suppressed_levels() -> Optional[str]:
    """Get the current suppress level."""
    return _config.suppress_levels


def get_logger(name: str) -> EnhancedLogger:
    """Get or create an enhanced logger instance."""
    if not name:
        raise ValueError("Logger name cannot be empty")

    with _logger_lock:
        if name not in _loggers:
            _loggers[name] = EnhancedLogger(name)
        return _loggers[name]


def profile_operation(operation: str, slow_threshold_ms: int = None):
    """Decorator for profiling operations (uses default logger)."""
    if slow_threshold_ms is None:
        slow_threshold_ms = _config.SLOW_OPERATION_THRESHOLD_MS

    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        return logger.profile_operation(operation, slow_threshold_ms)(func)

    return decorator


@contextmanager
def operation_context(logger_name: str, **context):
    """Context manager for operation context (convenience function)."""
    logger = get_logger(logger_name)
    with logger.operation_context(**context):
        yield


@contextmanager
def profile_context(logger_name: str, operation: str):
    """Context manager for performance profiling (convenience function)."""
    logger = get_logger(logger_name)
    with logger.profile_context(operation):
        yield


def detect_debug_mode():
    """Detect debug mode from command line arguments."""
    import sys

    if "-d" in sys.argv or "--debug" in sys.argv:
        set_debug_mode(True)

        for arg in sys.argv:
            if arg.startswith("--suppress="):
                suppress_value = arg.split("=", 1)[1]
                if suppress_value in ("debug", "info", "all"):
                    set_suppress_levels(suppress_value)
                break

        return True
    return False


# Auto-detect debug mode on import
detect_debug_mode()
