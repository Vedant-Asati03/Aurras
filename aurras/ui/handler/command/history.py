"""
History commands for Aurras Music Player.

This module contains all history-related commands such as viewing and managing play history.
"""

import logging
from aurras.core.settings import SETTINGS
from aurras.utils.command.processors import history_processor

logger = logging.getLogger(__name__)
COMMAND_SETTINGS = SETTINGS.command


def register_history_commands(registry):
    """Register all history-related commands to the central registry."""
    registry.register_command(
        name=COMMAND_SETTINGS.display_history,
        function=history_processor.show_history,
        description="Show play history",
        parameter_help="[limit=30]",
        requires_args=False,
        category="History",
    )

    registry.register_command(
        name=COMMAND_SETTINGS.play_previous_song,
        function=history_processor.play_previous_song,
        description="Play the previous song",
        parameter_help=None,
        requires_args=False,
        category="Playback",
    )

    registry.register_command(
        name=COMMAND_SETTINGS.clear_listening_history,
        function=history_processor.clear_history,
        description="Clear play history",
        parameter_help=None,
        requires_args=False,
        category="History",
    )

    logger.debug("History commands registered")
