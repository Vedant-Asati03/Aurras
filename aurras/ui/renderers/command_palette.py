"""
Command Palette Renderer for Aurras Music Player.
"""

from aurras.utils.logger import get_logger
from aurras.ui.core.registry import command_registry

logger = get_logger("aurras.ui.command_palette", log_to_console=False)


class CommandPalette:
    """
    Command palette UI component for discovering and executing commands.

    This class provides a searchable interface for users to find and execute
    commands in a convenient way.
    """

    def __init__(self):
        """Initialize the command palette with categories and commands."""

    def create_commands_mapping(self):
        """
        Build the commands dictionary with metadata from the central registry.

        Returns:
            Dictionary mapping command IDs to command metadata
        """
        commands_dict = {}

        commands_info = command_registry.get_commands_help()
        commands_dict = {
            command["name"]: f"{command['usage']}   {command['description']}"
            for command in commands_info
        }

        return commands_dict
