"""
Player commands for Aurras Music Player.

This module contains all player-related commands such as play, pause, volume control, etc.
"""

import logging

from ...core.registry import CommandRegistry
from ....player.offline import LocalPlaybackHandler
from ....utils.command.processors.player import processor

logger = logging.getLogger(__name__)
command_registry = CommandRegistry()


def register_player_commands():
    """Register all player-related commands to the central registry."""
    command_registry.register_command(
        name="play",
        function=processor.play_song,
        description="Play a song",
        parameter_help="<song_name>",
        requires_args=True,
        category="Playback",
    )

    command_registry.register_command(
        name="download_song",
        function=processor.download_song,
        description="Download a song",
        parameter_help="<song_name>",
        requires_args=True,
        category="Download",
    )

    command_registry.register_command(
        name="offline",
        function=lambda: LocalPlaybackHandler().listen_song_offline(),
        description="Play downloaded songs",
        parameter_help=None,
        requires_args=False,
        category="Playback",
    )

    logger.debug("Player commands registered")
