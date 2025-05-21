"""
Help renderer for Aurras Music Player.

This module provides components to display help information about commands and shorthands.
"""

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.ui.core.registry import command_registry, shortcut_registry
from aurras.core.player.offline import LocalPlaybackHandler

logger = get_logger("aurras.ui.renderers.options_palette", log_to_console=False)


class OptionsMenuRenderer:
    """Renderer for displaying help information about commands and shorthands."""

    def __init__(self):
        """Initialize the options menu renderer."""

    def create_options_mapping(self):
        """
        Build the options dictionary with metadata from the central registry.

        Returns:
            Dictionary mapping option IDs to option metadata
        """
        options_dict = {
            "help": "Display help information about available commands",
            "local-groove": "Play downloaded songs",
            "discover": "Discover new songs (Upcoming feature)",
            "disco": "Mode with changing colors and patterns (Upcoming feature)",
        }

        return options_dict


options = OptionsMenuRenderer().create_options_mapping()
logger.debug("Options menu initialized.")


def display_help():
    """Display help information about available commands in a user-friendly format."""

    # Welcome message
    welcome_message = console.style_text(
        text="Hello there! Welcome to AURRAS 󰽰",
        style_key="primary",
        text_style="bold underline",
    )
    console.rule(title=welcome_message, style=console.accent)

    # help message
    console.print_info(
        "\nReady to elevate your music experience? Let's get you started!",
    )

    console.print_info(
        "Your search bar is not a simple text box; it's a command center!\n  Type '>' to enter into the command palette\n  '?' to see all the unique App features\n  Type any of the available commands or shorthands for faster access to features \n  Just type any song name to search for it.\n",
    )

    console.print_info(
        "Here's a list of all commands and shorthands. Use them by typing the command and pressing Enter."
    )
    commands_dict = {
        command["name"]: f"{command['description']}    usage: {command['usage']}"
        for command in command_registry.get_commands_help()
    }
    console.print_info("\nCommands:")
    for name, desc in commands_dict.items():
        console.style_text(
            text=f"  {name} 󰑃 {desc}",
            style_key="accent",
            text_style="bold",
            print_it=True,
        )

    shorthands_dict = {
        shorthand["prefix"]: shorthand["description"]
        for shorthand in shortcut_registry.get_shorthands_help()
    }
    console.print_info("Shorthands:")
    for prefix, desc in shorthands_dict.items():
        console.style_text(
            text=f"  {prefix} 󰑃 {desc}",
            style_key="secondary",
            text_style="bold",
            print_it=True,
        )

    # Additional information
    console.print_info("\nFor more detailed information, check the documentation.")

    # Footer message
    outrow_message = console.style_text(
        text="Happy Listening! ✨",
        style_key="primary",
        text_style="bold underline",
    )
    console.rule(title=outrow_message, style=console.accent)


def discover_new_songs():
    """Discover new songs."""
    console.print_info("Discovering new songs... (This feature is coming soon!)")


def disco_mode():
    """Activate disco mode with changing colors and patterns."""
    console.print_info("Disco mode activated! (This feature is coming soon!)")


def execute_option(option: str) -> bool:
    """
    Execute the selected option.

    Args:
        option_id: The ID of the selected option
    """
    if option not in options:
        return False

    option_method_dict = {
        "help": display_help,
        "local-groove": LocalPlaybackHandler().listen_song_offline,
        "discover": discover_new_songs,
        "disco": disco_mode,
    }

    func = option_method_dict.get(option)

    if func:
        func()
    else:
        logger.warning(f"Unknown option ID: {option}")
        return False

    return True
