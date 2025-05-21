"""
These commands are gonna be only accessible from command palette and not from commands shortcuts.
"""

from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.ui.core.registry import command_registry
from aurras.utils.command.processors import settings_processor

logger = get_logger("aurras.ui.handler.command.settings", log_to_console=False)
COMMAND_SETTINGS = SETTINGS.command


def register_settings_commands():
    """Register all settings-related commands to the central registry."""
    command_registry.register_command(
        name="settings:view-settings",
        function=settings_processor.list_settings,
        description="View current settings",
        parameter_help=None,
        requires_args=False,
        category="Interface",
    )

    command_registry.register_command(
        name="set",
        function=settings_processor.set_setting,
        description="Set a setting",
        parameter_help="set <setting> <value>",
        requires_args=True,
        category="Settings",
    )

    command_registry.register_command(
        name=COMMAND_SETTINGS.toggle_lyrics,
        function=settings_processor.toggle_setting,
        description="Toggle lyrics visibility",
        parameter_help=None,
        requires_args=False,
        category="Interface",
    )

    logger.debug("Settings commands registered")
