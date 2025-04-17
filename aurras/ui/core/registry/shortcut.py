"""
Shortcut Registry for Aurras Music Player.

This module provides a centralized registry for all keyboard shortcuts and command shorthands
in the application. It allows registering, executing, and retrieving information about shortcuts.
"""

import logging
from typing import Dict, List

from ..registry.command import CommandRegistry

logger = logging.getLogger(__name__)


class ShortcutRegistry:
    """
    Centralized registry for all shortcuts in the application.

    This class manages the registration and execution of shortcuts,
    providing a unified interface for all shortcut operations.
    """

    def __init__(self):
        """Initialize the shortcut registry."""
        self._shorthands = []
        self._command_registry = CommandRegistry()

    def register_shorthand(
        self, prefix: str, command: str, description: str, strip_prefix: bool = True
    ):
        """
        Register a new shorthand command.

        Args:
            prefix: The shorthand prefix
            command: The actual command to execute
            description: Short description of what the shorthand does
            strip_prefix: Whether to strip the prefix when passing args
        """
        self._shorthands.append(
            {
                "prefix": prefix,
                "command": command,
                "description": description,
                "strip_prefix": strip_prefix,
            }
        )
        logger.debug(f"Registered shorthand: {prefix} → {command}")

    def check_shorthand_commands(self, input_text: str) -> bool:
        """
        Check if input matches any shorthand commands and execute if it does.

        Args:
            input_text: The raw input text to check

        Returns:
            True if a shorthand was executed, False otherwise
        """
        for shorthand in self._shorthands:
            prefix = shorthand["prefix"]

            if input_text.startswith(prefix):
                command = shorthand["command"]

                if shorthand["strip_prefix"]:
                    args = input_text[len(prefix) :].strip()
                else:
                    # Parse arguments from the full string (like cleanup_cache 30)
                    _, args_list = self.command_registry.parse_command(input_text)
                    args = args_list[0] if args_list else ""

                if args:
                    logger.debug(
                        f"Executing shorthand command: {command} with args: {args}"
                    )
                    return self.command_registry.execute_command(command, [args])
                else:
                    logger.debug(f"Executing shorthand command: {command}")
                    return self.command_registry.execute_command(command)

        return False

    def get_shorthands_help(self) -> List[Dict[str, str]]:
        """
        Get a formatted list of all available shorthand commands.

        Returns:
            List of shorthand info dictionaries
        """
        shorthands = []

        for shorthand in self._shorthands:
            prefix = shorthand["prefix"].strip()
            command = shorthand["command"]
            example = (
                f"{prefix}example" if shorthand["strip_prefix"] else prefix + "example"
            )

            shorthands.append(
                {
                    "prefix": prefix,
                    "command": command,
                    "description": shorthand["description"],
                    "example": example,
                }
            )

        # Sort by prefix
        return sorted(shorthands, key=lambda x: x["prefix"])

    def clear(self):
        """Clear all registered shorthands."""
        self._shorthands = []
