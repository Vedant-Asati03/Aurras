"""
Player commands for Aurras Music Player.

This module contains all player-related commands such as play, pause, volume control, etc.
"""

from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.ui.core.registry import command_registry
# from aurras.core.player.offline import LocalPlaybackHandler
from aurras.utils.command.processors import player_processor

logger = get_logger("aurras.ui.handler.command.player", log_to_console=False)
COMMAND_SETTINGS = SETTINGS.command


def register_player_commands():
    """Register all player-related commands to the central registry."""
    command_registry.register_command(
        name=COMMAND_SETTINGS.download_song,
        function=player_processor.download_song,
        description="Download a song",
        parameter_help="<song_name>",
        requires_args=True,
        category="Download",
    )

    # command_registry.register_command(
    #     name=COMMAND_SETTINGS.play_offline,
    #     function=lambda: LocalPlaybackHandler().listen_song_offline,
    #     description="Play downloaded songs",
    #     parameter_help=None,
    #     requires_args=False,
    #     category="Playback",
    # )

    logger.debug("Player commands registered")
