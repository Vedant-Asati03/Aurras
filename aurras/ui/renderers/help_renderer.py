"""
Help renderer for Aurras Music Player.

This module provides components to display help information about commands and shorthands.
"""

import logging
from rich.console import Console

from ..core.registry.command import command_registry
from ..core.registry.shortcut import shortcut_registry
from ...utils.theme_helper import ThemeHelper

logger = logging.getLogger(__name__)
console = Console()


class HelpRenderer:
    """Renders help information about commands and shortcuts."""

    def display_help(self):
        """Display help information about available commands in a user-friendly format."""
        theme_styles = ThemeHelper.get_theme_colors()
        primary_color = theme_styles.get("primary", "cyan")
        accent_color = theme_styles.get("accent", "green")

        console.print(
            f"\n[bold {primary_color}]Available Commands:[/bold {primary_color}]"
        )

        # Display command information by category
        categories = command_registry.get_all_categories()

        for category in categories:
            commands = [
                cmd
                for cmd in command_registry.get_commands_help()
                if cmd.get("category") == category
            ]

            if commands:
                console.print(
                    f"\n[bold {primary_color}]{category} Commands:[/bold {primary_color}]"
                )

                for cmd in sorted(commands, key=lambda x: x["name"]):
                    console.print(
                        f"[bold {accent_color}]{cmd['usage']}[/bold {accent_color}] - "
                        f"{cmd['description']}"
                    )

        console.print(
            f"\n[bold {primary_color}]Shorthand Commands:[/bold {primary_color}]"
        )

        # Display shorthand information
        for shorthand in shortcut_registry.get_shorthands_help():
            console.print(
                f"[bold {accent_color}]{shorthand['prefix']}...[/bold {accent_color}] - "
                f"{shorthand['description']} (runs '{shorthand['command']}')"
            )
