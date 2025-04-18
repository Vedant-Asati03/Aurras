"""
Player commands for Aurras Music Player.

This module contains all player-related commands such as play, pause, volume control, etc.
"""

import logging

from ...core.registry import CommandRegistry
from ....core.settings import load_settings
from ....utils.command.processors.player import processor
from ....player.offline import LocalPlaybackHandler

logger = logging.getLogger(__name__)
COMMAND_SETTINGS = load_settings().command


def register_player_commands(registry: CommandRegistry):
    """Register all player-related commands to the central registry."""
    registry.register_command(
        name=COMMAND_SETTINGS.download_song,
        function=processor.download_song,
        description="Download a song",
        parameter_help="<song_name>",
        requires_args=True,
        category="Download",
    )

    registry.register_command(
        name=COMMAND_SETTINGS.play_offline,
        function=lambda: LocalPlaybackHandler().listen_song_offline(),
        description="Play downloaded songs",
        parameter_help=None,
        requires_args=False,
        category="Playback",
    )

    logger.debug("Player commands registered")
