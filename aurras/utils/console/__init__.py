"""
Console utilities for rich text output and component-based UI.

This package contains utilities for working with Rich console output,
including components, formatters, and renderers.
"""

from aurras.utils.logger import get_logger
from aurras.utils.console.manager import get_console, apply_gradient_to_text

logger = get_logger("aurras.utils.console", log_to_console=False)

console = get_console()
logger.debug("Console initialized")

__all__ = [
    "console",
    "apply_gradient_to_text",
]
