"""
History commands for Aurras Music Player.

This module contains all history-related commands such as viewing and managing play history.
"""

import logging
from ...core.registry.command import CommandRegistry
from ....utils.command.processors.history import HistoryProcessor

logger = logging.getLogger(__name__)

history_processor = HistoryProcessor()


def register_history_commands(registry: CommandRegistry):
    """Register all history-related commands to the central registry."""
    registry.register_command(
        name="history",
        function=history_processor.display_history,
        description="Show play history",
        parameter_help="[limit=30]",
        requires_args=False,
        category="History",
    )

    registry.register_command(
        name="previous",
        function=history_processor.play_previous_song,
        description="Play the previous song",
        parameter_help=None,
        requires_args=False,
        category="Playback",
    )

    registry.register_command(
        name="clear_history",
        function=history_processor.clear_history,
        description="Clear play history",
        parameter_help=None,
        requires_args=False,
        category="History",
    )

    logger.debug("History commands registered")
