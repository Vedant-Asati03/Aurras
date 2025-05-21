"""
Command Registry for Aurras Music Player.

This module provides a centralized registry for all commands in the application.
It allows registering, executing, and retrieving information about commands.
"""

import re
import shlex
from typing import Dict, Callable, Optional, List, Tuple

from aurras.utils.console import console
from aurras.utils.logger import get_logger

logger = get_logger("aurras.ui.core.registry.command", log_to_console=False)

# COMMAND_PATTERN = re.compile(r"^(\w+)(?:\s+(.*))?$")
COMMAND_PATTERN = re.compile(r"^([\w\-:]+)(?:\s+(.*))?$")


class CommandRegistry:
    """
    Centralized registry for all commands in the application.

    This class manages the registration and execution of commands,
    providing a unified interface for all command operations.
    """

    def __init__(self):
        """Initialize the command registry."""
        self._commands = {}

    def register_command(
        self,
        name: str,
        function: Callable,
        description: str,
        parameter_help: Optional[str] = None,
        requires_args: bool = False,
        category: str = "General",
    ):
        """
        Register a new command to the command registry.

        Args:
            name: Command name (without parameters)
            function: The function to execute when command is called
            description: Short description of what the command does
            parameter_help: Help text showing parameter format
            requires_args: Whether this command requires arguments
            category: The category this command belongs to
        """
        self._commands[name] = {
            "function": function,
            "description": description,
            "parameter_help": parameter_help,
            "requires_args": requires_args,
            "category": category,
        }
        logger.debug(f"Registered command: {name}")

    def execute_command(self, command: str, args: List[str] = None) -> bool:
        """
        Execute a command with arguments from the command registry.

        Args:
            command: The command name to execute
            args: List of arguments to pass to the command

        Returns:
            True if command was handled, False otherwise
        """
        args = [] if args is None else args

        if not self.has_command(command):
            return False

        command_info = self._commands[command]
        require_args = command_info["requires_args"]
        param_help = command_info["parameter_help"] or "<arguments>"

        if require_args and not args:
            console.print_error(f"'{command}' requires parameters: {param_help}")

            logger.debug(f"Command '{command}' requires parameters: {param_help}")
            return True

        try:
            func = command_info["function"]

            if args and hasattr(func, "__code__") and func.__code__.co_argcount > 0:
                func(*args) if len(args) > 1 else func(args[0])
            else:
                func()

            return True

        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}", exc_info=True)
            console.print_error(f"Error executing '{command}': {str(e)}")
            return True

    def parse_command(self, input_text: str) -> Tuple[str, List[str]]:
        """
        Parse a command string into command name and arguments.

        Args:
            input_text: The raw command string

        Returns:
            A tuple of (command_name, argument_list)
        """
        match = COMMAND_PATTERN.match(input_text)

        if not match:
            return ("", [])

        command = match.group(1)
        args_str = match.group(2) or ""

        try:
            args = shlex.split(args_str) if args_str else []
        except ValueError:
            args = args_str.split()

        return (command, args)

    def get_command(self, name: str) -> Optional[Dict]:
        """
        Get information about a specific command.

        Args:
            name: The name of the command to get

        Returns:
            Command information dictionary or None if not found
        """
        return self._commands.get(name)

    def has_command(self, name: str) -> bool:
        """
        Check if a command exists in the registry.

        Args:
            name: The name of the command to check

        Returns:
            True if the command exists, False otherwise
        """
        return name in self._commands

    def get_commands_by_category(self, category: str) -> Dict[str, Dict]:
        """
        Get all commands in a specific category.

        Args:
            category: The category to filter by

        Returns:
            Dictionary of commands in the requested category
        """
        return {
            name: command_info
            for name, command_info in self._commands.items()
            if command_info.get("category", "General") == category
        }

    def get_all_categories(self) -> List[str]:
        """
        Get a list of all command categories.

        Returns:
            List of unique command categories
        """
        categories = set()

        for command_info in self._commands.values():
            categories.add(command_info.get("category", "General"))

        return sorted(list(categories))

    def get_commands_help(self) -> List[Dict[str, str]]:
        """
        Get a formatted list of all available commands and their descriptions.

        Returns:
            List of command info dictionaries with name, description, and usage
        """
        commands = []

        for command_name, cmd_info in self._commands.items():
            param_help = cmd_info["parameter_help"] or ""
            usage = f"{command_name} {param_help}".strip()

            commands.append(
                {
                    "name": command_name,
                    "description": cmd_info["description"],
                    "usage": usage,
                    "category": cmd_info.get("category", "General"),
                    "requires_args": cmd_info["requires_args"],
                }
            )

        return sorted(commands, key=lambda x: x["name"])

    def get_command_list(self) -> List[str]:
        """
        Get a list of all registered command names.

        Returns:
            List of command names
        """
        return sorted(list(self._commands.keys()))

    def clear(self):
        """Clear all registered commands."""
        self._commands = {}
