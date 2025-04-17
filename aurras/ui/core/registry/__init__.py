"""
Registry Module for Commands, Shortcuts and Input Processors

This module provides a centralized registry for all commands, shortcuts, and input processors
"""

from .command import CommandRegistry
from .shortcut import ShortcutRegistry
from .completer import CompleterRegistry


__all__ = [
    "CommandRegistry",
    "ShortcutRegistry",
    "CompleterRegistry",
]
