"""
Spotify integration commands for Aurras Music Player.

This module contains all Spotify-related commands such as setup, import, etc.
"""

import logging
from aurras.core.settings import SETTINGS
from aurras.ui.core.registry import command_registry
from aurras.utils.command.processors import spotify_processor

logger = logging.getLogger(__name__)
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
