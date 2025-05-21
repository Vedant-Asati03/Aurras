"""
These commands are gonna be only accessible from command palette and not from commands shortcuts.
"""

from aurras.utils.logger import get_logger
from aurras.ui.core.registry import command_registry
from aurras.utils.command.processors import theme_processor

logger = get_logger("aurras.ui.handler.command.theme", log_to_console=False)


def register_theme_commands():
    """Register all settings-related commands to the central registry."""
    command_registry.register_command(
        name="themes:view-themes",
        function=theme_processor.list_themes,
        description="View available themes",
        parameter_help=None,
        requires_args=False,
        category="Theme",
    )

    command_registry.register_command(
        name="themes:current-theme",
        function=theme_processor.display_current_theme,
        description="Display current theme",
        parameter_help=None,
        requires_args=False,
        category="Theme",
    )

    command_registry.register_command(
        name="apply",
        function=theme_processor.set_theme,
        description="Apply a theme",
        parameter_help="apply <theme_name>",
        requires_args=True,
        category="Theme",
    )

    logger.debug("Settings commands registered")
