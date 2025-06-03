"""
System commands for Aurras Music Player.

This module contains all system-related commands such as cache management, settings, etc.
"""

from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.ui.core.registry import command_registry
from aurras.utils.command.processors import system_processor, self_processor

logger = get_logger("aurras.ui.handler.command.system", log_to_console=False)
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
        parameter_help="<days=30>",
        requires_args=False,
        category="System",
    )

    command_registry.register_command(
        name="self:version-info",
        function=self_processor.get_version_info,
        description="Show Aurras version and installation info",
        parameter_help=None,
        requires_args=False,
        category="System",
    )

    logger.debug("System commands registered")
