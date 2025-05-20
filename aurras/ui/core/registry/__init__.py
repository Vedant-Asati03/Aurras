"""
Registry Module for Commands, Shortcuts and Input Processors

This module provides a centralized registry for all commands, shortcuts, and input processors
"""

from aurras.utils.logger import get_logger
from aurras.ui.core.registry.command import CommandRegistry
from aurras.ui.core.registry.shortcut import ShortcutRegistry
from aurras.ui.core.registry.completer import CompleterRegistry

logger = get_logger("aurras.ui.core.registry", log_to_console=False)

command_registry = CommandRegistry()
logger.debug("Command registry initialized.")
shortcut_registry = ShortcutRegistry(command_registry=command_registry)
logger.debug("Shortcut registry initialized.")


__all__ = [
    "CompleterRegistry",
    "command_registry",
    "shortcut_registry",
]
