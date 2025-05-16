"""
Registry Module for Commands, Shortcuts and Input Processors

This module provides a centralized registry for all commands, shortcuts, and input processors
"""

from aurras.ui.core.registry.command import CommandRegistry
from aurras.ui.core.registry.shortcut import ShortcutRegistry
from aurras.ui.core.registry.completer import CompleterRegistry

command_registry = CommandRegistry()
shortcut_registry = ShortcutRegistry(command_registry=command_registry)


__all__ = [
    "CompleterRegistry",
    "command_registry",
    "shortcut_registry",
]
