"""
Spotify integration commands for Aurras Music Player.

This module contains all Spotify-related commands such as setup, import, etc.
"""

import logging
from ...core.registry.command import CommandRegistry
from ...command_handler import InputCases

logger = logging.getLogger(__name__)

command_registry = CommandRegistry()
input_cases = InputCases()


def register_spotify_commands():
    """Register all Spotify-related commands to the central registry."""
    command_registry.register_command(
        name="setup_spotify",
        function=input_cases.setup_spotify,
        description="Set up Spotify integration",
        parameter_help=None,
        requires_args=False,
        category="Services",
    )

    logger.debug("Spotify commands registered")
