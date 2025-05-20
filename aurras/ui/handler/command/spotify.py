"""
Spotify integration commands for Aurras Music Player.

This module contains all Spotify-related commands such as setup, import, etc.
"""

from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.ui.core.registry import command_registry
from aurras.utils.command.processors import spotify_processor

logger = get_logger("aurras.ui.handler.command.spotify", log_to_console=False)
COMMAND_SETTINGS = SETTINGS.command


def register_spotify_commands():
    """Register all Spotify-related commands to the central registry."""
    command_registry.register_command(
        name=COMMAND_SETTINGS.setup_spotify,
        function=spotify_processor.setup_spotify,
        description="Set up Spotify integration",
        parameter_help=None,
        requires_args=False,
        category="Services",
    )

    logger.debug("Spotify commands registered")
