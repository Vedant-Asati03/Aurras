"""
Custom lexer for Aurras input highlighting.

This module provides a lexer for highlighting commands and shorthands
in the input field according to the current theme.
"""

import re
from typing import Callable, Dict, List, Optional, Tuple

from prompt_toolkit.lexers import Lexer
from prompt_toolkit.document import Document

from aurras.utils.console import console
from aurras.core.settings import SETTINGS


class InputLexer(Lexer):
    """
    Custom lexer for Aurras input highlighting.

    Highlights:
    - Command palette prefix (>)
    - Options menu prefix (?)
    - Shorthand prefixes (v, p, d, etc.)
    - Known commands
    - Arguments
    """

    def __init__(self, command_registry=None, shorthand_registry=None):
        """
        Initialize the lexer with command and shorthand registries.

        Args:
            command_registry: Registry of available commands
            shorthand_registry: Registry of available shorthands
        """
        self.command_registry = command_registry
        self.shorthand_registry = shorthand_registry
        self.update_theme_colors()

    def update_theme_colors(self):
        """Update the theme colors for syntax highlighting."""
        self.command_palette_style = f"class:command-palette fg:{console.accent} bold"
        self.options_menu_style = f"class:options-menu fg:{console.secondary} bold"
        self.shorthand_style = f"class:shorthand fg:{console.primary}"
        self.command_style = f"class:command fg:{console.secondary}"
        self.argument_style = f"class:argument fg:{console.text}"
        self.default_style = f"class:text fg:{console.text}"

    def get_commands(self) -> List[str]:
        """Get a list of all available commands."""
        if not self.command_registry:
            return []
        return self.command_registry.get_command_list()

    def get_shorthands(self) -> Dict[str, str]:
        """Get a dictionary of available shorthands."""
        if not self.shorthand_registry:
            return {}
        return {
            prefix: command
            for prefix, command in self.shorthand_registry.get_shorthand_dict().items()
        }

    def _process_prefix_command(
        self, line: str, prefix: str, prefix_style: str
    ) -> List[Tuple[str, str]]:
        """
        Process a line that starts with a prefix character.

        Args:
            line: The input line
            prefix: The prefix character ('>' or '?')
            prefix_style: The style to apply to the prefix

        Returns:
            A list of (style, text) tuples for the line
        """
        result = [(prefix_style, prefix)]
        remaining = line[len(prefix) :].lstrip()

        if not remaining:
            return result

        if " " in remaining:
            cmd, args = remaining.split(" ", 1)
            result.extend(
                [
                    (self.command_style, cmd),
                    (self.default_style, " "),
                    (self.argument_style, args),
                ]
            )
        else:
            result.append((self.command_style, remaining))

        return result

    def _process_shorthand(self, line: str, prefix: str) -> List[Tuple[str, str]]:
        """
        Process a line that starts with a shorthand prefix.

        Args:
            line: The input line
            prefix: The shorthand prefix

        Returns:
            A list of (style, text) tuples for the line
        """
        result = [(self.shorthand_style, prefix)]
        args = line[len(prefix) :]
        if args:
            result.append((self.argument_style, args))
        return result

    def _process_direct_command(
        self, line: str, commands: List[str]
    ) -> Optional[List[Tuple[str, str]]]:
        """
        Process a line as a direct command.

        Args:
            line: The input line
            commands: List of valid commands

        Returns:
            A list of (style, text) tuples for the line, or None if no command match
        """
        for cmd in commands:
            pattern = f"^{cmd}\\b"
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                cmd_part = match.group(0)
                result = [(self.command_style, cmd_part)]

                remainder = line[len(cmd_part) :].lstrip()
                if remainder:
                    result.extend(
                        [(self.default_style, " "), (self.argument_style, remainder)]
                    )
                return result
        return None

    def lex_document(
        self, document: Document
    ) -> Callable[[int], List[Tuple[str, str]]]:
        """
        Lex the input document and return a function to get the styling for each line.

        Args:
            document: The document to lex

        Returns:
            A function that given a line number, returns a list of (style, text) tuples
        """
        self.update_theme_colors()  # Ensure we have the latest theme colors

        def get_line(lineno: int) -> List[Tuple[str, str]]:
            """
            Get the styling for a specific line.

            Args:
                lineno: The line number to style

            Returns:
                A list of (style, text) tuples for the given line
            """
            if lineno >= len(document.lines):
                return []

            line = document.lines[lineno]

            if not line:
                return []

            if line.startswith(SETTINGS.options_menu_key):
                return self._process_prefix_command(
                    line, SETTINGS.options_menu_key, self.options_menu_style
                )

            if line.startswith(SETTINGS.command_palette_key):
                return self._process_prefix_command(
                    line, SETTINGS.command_palette_key, self.command_palette_style
                )

            commands = self.get_commands()
            command_result = self._process_direct_command(line, commands)
            if command_result:
                return command_result

            shorthands = self.get_shorthands()
            for prefix, command in shorthands.items():
                if line.startswith(prefix):
                    return self._process_shorthand(line, prefix)

            return [(self.default_style, line)]

        return get_line
