"""
Help renderer for Aurras Music Player.

This module provides components to display help information about commands and shorthands.
"""

from aurras.utils.logger import get_logger
from aurras.utils.console import console
from aurras.ui.core.registry import command_registry
from aurras.ui.core.registry.shortcut import shortcut_registry

logger = get_logger("aurras.ui.renderers.options_palette", log_to_console=False)


class OptionsMenuRenderer:
    """Renders help information about commands and shortcuts."""

    # def display_help(self):
    #     """Display help information about available commands in a user-friendly format."""
    #     console.style_text(text="Available Commands", style_key="primary")

    #     # Display command information by category
    #     categories = command_registry.get_all_categories()

    #     for category in categories:
    #         commands = [
    #             cmd
    #             for cmd in command_registry.get_commands_help()
    #             if cmd.get("category") == category
    #         ]

    #         if commands:
    #             console.style_text(
    #                 text=f"{category} Commands",
    #                 style_key="primary_color",
    #                 text_style="bold",
    #             )

    #             for cmd in sorted(commands, key=lambda x: x["name"]):
    #                 console.style_text(
    #                     text=f"{cmd['usage']}",
    #                     style_key="accent_color",
    #                     text_style="bold",
    #                 )

    #     console.style_text(
    #         text="Shorthand Commands",
    #         style_key="primary_color",
    #         text_style="bold",
    #     )

    #     for shorthand in shortcut_registry.get_shorthands_help():
    #         console.style_text(
    #             text=f"{shorthand['prefix']}... - {shorthand['description']} (runs '{shorthand['command']}')",
    #             style_key="accent_color",
    #             text_style="bold",
    #         )
