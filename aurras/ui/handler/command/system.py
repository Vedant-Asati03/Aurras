"""
System commands for Aurras Music Player.

This module contains all system-related commands such as cache management, settings, etc.
"""

import logging

from ...command_handler import InputCases
from ...core.registry.command import CommandRegistry

logger = logging.getLogger(__name__)

input_cases = InputCases()


def register_system_commands(registry: CommandRegistry):
    """Register all system-related commands to the central registry."""
    registry.register_command(
        name="cache",
        function=input_cases.show_cache_info,
        description="Show cache information",
        parameter_help=None,
        requires_args=False,
        category="System",
    )

    registry.register_command(
        name="cleanup",
        function=input_cases.cleanup_cache,
        description="Clean up cache",
        parameter_help="[days=30]",
        requires_args=False,
        category="System",
    )

    registry.register_command(
        name="lyrics",
        function=input_cases.toggle_lyrics,
        description="Toggle lyrics display",
        parameter_help=None,
        requires_args=False,
        category="Interface",
    )

    logger.debug("System commands registered")
