"""
Core UI components for Aurras Music Player.

This package contains the core components that power the UI functionality:
- command_registry: Centralized registry for commands
- shortcut_registry: Centralized registry for shortcuts
- input_processor: Processes and routes user input
"""

from .input_processor import input_processor
from .registry.command import CommandRegistry
from .registry.shortcut import ShortcutRegistry

__all__ = ["input_processor", "CommandRegistry", "ShortcutRegistry"]
