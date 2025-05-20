"""
Core UI components for Aurras Music Player.

This package contains the core components that power the UI functionality:
- command_registry: Centralized registry for commands
- shortcut_registry: Centralized registry for shortcuts
- input_processor: Processes and routes user input
"""

from aurras.utils.logger import get_logger
from aurras.ui.core.input_processor import InputProcessor

logger = get_logger("aurras.ui.core", log_to_console=False)

input_processor = InputProcessor()
logger.debug("Input processor initialized.")

__all__ = ["input_processor"]
