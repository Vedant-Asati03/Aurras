"""
System commands for Aurras Music Player.

This module contains all system-related commands such as cache management, settings, etc.
"""

import logging

from aurras.core.settings import SETTINGS
from aurras.ui.core.registry import command_registry
from aurras.utils.command.processors import system_processor

logger = logging.getLogger(__name__)
COMMAND_SETTINGS = SETTINGS.command


def register_system_commands():
    """Register all system-related commands to the central registry."""
    command_registry.register_command(
        name=COMMAND_SETTINGS.display_cache_info,
        function=system_processor.show_cache_info,
        description="Show cache information",
        parameter_help=None,
        requires_args=False,
        category="System",
    )

    command_registry.register_command(
        name=COMMAND_SETTINGS.cleanup_cache,
        function=system_processor.cleanup_cache,
        description="Clean up cache",
        parameter_help="[days=30]",
        requires_args=False,
        category="System",
    )

    command_registry.register_command(
        name=COMMAND_SETTINGS.toggle_lyrics,
        function=system_processor.toggle_lyrics,
        description="Toggle lyrics display",
        parameter_help=None,
        requires_args=False,
        category="Interface",
    )

    logger.debug("System commands registered")
