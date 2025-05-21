"""
History commands for Aurras Music Player.

This module contains all history-related commands such as viewing and managing play history.
"""

from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.ui.core.registry import command_registry
from aurras.utils.command.processors import history_processor

logger = get_logger("aurras.ui.handler.command.history", log_to_console=False)
COMMAND_SETTINGS = SETTINGS.command


def register_history_commands():
    """Register all history-related commands to the central registry."""
    command_registry.register_command(
        name=COMMAND_SETTINGS.display_history,
        function=history_processor.show_history,
        description="Show play history",
        parameter_help="<limit=30>",
        requires_args=False,
        category="History",
    )

    command_registry.register_command(
        name=COMMAND_SETTINGS.play_previous_song,
        function=history_processor.play_previous_song,
        description="Play the previous song",
        parameter_help=None,
        requires_args=False,
        category="Playback",
    )

    command_registry.register_command(
        name=COMMAND_SETTINGS.clear_listening_history,
        function=history_processor.clear_history,
        description="Clear play history",
        parameter_help=None,
        requires_args=False,
        category="History",
    )

    logger.debug("History commands registered")
