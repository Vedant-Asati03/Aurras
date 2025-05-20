"""
Spotify Setup Module

This module provides functionality for setting up Spotify API credentials.
"""

from typing import Optional, Tuple

from aurras.utils.console import console
from aurras.utils.logger import get_logger

logger = get_logger("aurras.services.spotify.setup", log_to_console=False)

class SpotifySetup:
    """Class for setting up Spotify API credentials."""

    def __init__(self):
        """Initialize the SpotifySetup."""

    def _styled_prompt(self, message: str, password: bool) -> str:
        """
        Prompt the user for input with a styled message.

        Args:
            message (str): The message to display in the prompt

        Returns:
            str: User input
        """

        return console.prompt(
            prompt_text=message,
            default="",
            password=password,
            show_default=False,
            show_choices=False,
        )

    def _prompt_user(self) -> Optional[Tuple[str, str] | None]:
        """
        Prompt user for Spotify API credentials.

        Returns:
            tuple: Client ID and Client Secret
        """
        console.print(
            "[bold blue]Please enter your Spotify API credentials:[/bold blue]"
        )
        client_id = self._styled_prompt(
            f"[bold {console.text}]Client ID  [/]", password=False
        )
        client_secret = self._styled_prompt(
            f"[bold {console.text}]Client Secret  [/]", password=True
        )

        if not client_id or not client_secret:
            return None

        return (client_id, client_secret)

    def setup_credentials(self):
        """
        Set up Spotify API credentials.

        Returns:
            bool: True if setup was successful, False otherwise
        """
        display_setup_instruction()
        client_id, client_secret = self._prompt_user()

        if not client_id or not client_secret:
            console.print_error("Invalid credentials. Please try again.")
            return False

        credentials = {
            "client_id": client_id,
            "client_secret": client_secret,
        }

        from aurras.services.spotify.cache import CredentialsCache

        cache = CredentialsCache()
        cache.store_credentials(credentials=credentials)
        return True


def display_setup_instruction():
    """
    Display setup instructions for Spotify API credentials.
    """
    from aurras.utils.console.renderer import ListDisplay

    instructions = ListDisplay(
        [
            "Go to the  (https://developer.spotify.com/dashboard/applications).",
            "Log in with your Spotify account.",
            "Click on 'Create an App'.",
            "Fill in the required fields (leave the optional fields empty) and click 'Create'.",
            "Copy your Client ID and Client Secret.",
            "Paste them into the prompts when setting up Aurras.",
        ],
        title="Spotify API Setup Instructions",
        show_indices=True,
        show_header=False,
    )
    console.print(instructions.render())
