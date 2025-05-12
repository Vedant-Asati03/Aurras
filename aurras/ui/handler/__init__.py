"""
UI Handlers for Aurras Music Player.

This package contains handlers for user input, shortcuts, settings, and keyboard input:
- input_handler: Main input handler using component-based architecture
- shorthand_handler: Registration of shorthand commands
- settings_handler: Management of application settings
- keyboard_shortcut_handler: Management of keyboard shortcuts and key bindings
"""

from aurras.ui.handler.command import register_all_commands
from aurras.ui.handler.shorthand import register_default_shorthands

__all__ = [
    "register_all_commands",
    "register_default_shorthands",
]
