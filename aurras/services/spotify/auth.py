"""
Spotify Authentication Module

This module handles all Spotify authentication operations including OAuth,
credential setup, and client creation.
"""

from typing import Dict, Optional, Any, Tuple
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from aurras.utils.console import console
from aurras.utils.logger import get_logger

logger = get_logger("aurras.services.spotify.auth", log_to_console=False)

SCOPE = "playlist-read-private"
REDIRECT_URI = "http://127.0.0.1:8080"


class SpotifyAuth:
    """
    Handles Spotify API authentication, credential management, and client creation.

    This class consolidates all authentication-related functionality including:
    - User credential setup
    - OAuth token management
    - Authenticated client creation
    """

    def __init__(self):
        """Initialize the SpotifyAuth."""
        self._cache = None

    @property
    def cache(self):
        """Get the credentials cache."""
        if self._cache is None:
            from .cache import SpotifyCredentialsCache

            self._cache = SpotifyCredentialsCache()
        return self._cache

    # =====================
    # Setup Methods
    # =====================

    def setup_credentials(self) -> bool:
        """
        Run the setup process for Spotify credentials.

        Returns:
            bool: True if setup was successful
        """
        try:
            self._display_setup_instructions()
            credentials = self._prompt_user()

            if not credentials:
                console.print_warning("Setup cancelled by user")
                return False

            client_id, client_secret = credentials

            oauth_manager = self._create_oauth_manager(client_id, client_secret)
            token_info = oauth_manager.get_access_token(as_dict=False)

            if not token_info:
                console.print_error("Failed to authenticate with Spotify")
                return False

            credentials_data = {
                "client_id": client_id,
                "client_secret": client_secret,
            }

            if not self.cache.store_credentials(credentials_data):
                console.print_error("Failed to save credentials")
                return False

            console.print_success("✓ Spotify credentials saved successfully!")
            return True

        except Exception as e:
            logger.error(f"Error during setup: {e}")
            console.print_error(f"Setup failed: {e}")
            return False

    def _display_setup_instructions(self):
        """Display setup instructions for Spotify API credentials."""
        from aurras.utils.console.renderer import ListDisplay

        instructions = ListDisplay(
            [
                "Go to the Spotify Developer Dashboard (https://developer.spotify.com/dashboard/applications).",
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

    def _prompt_user(self) -> Optional[Tuple[str, str]]:
        """
        Prompt user for Spotify API credentials.

        Returns:
            tuple: Client ID and Client Secret, or None if cancelled
        """
        console.style_text(
            text="Please enter your Spotify API credentials",
            style_key="accent",
            print_it=True,
        )

        client_id = self._styled_prompt("Client ID", password=False)

        if not client_id.strip():
            return None

        client_secret = self._styled_prompt("Client Secret", password=False)

        if not client_secret.strip():
            return None

        return client_id.strip(), client_secret.strip()

    def _styled_prompt(self, message: str, password: bool) -> str:
        """
        Prompt the user for input with a styled message.

        Args:
            message (str): The message to display in the prompt
            password (bool): Whether to hide the input

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

    # =====================
    # OAuth Methods
    # =====================

    def _create_oauth_manager(self, client_id: str, client_secret: str):
        """
        Create a SpotifyOAuth manager.

        Args:
            client_id (str): Spotify client ID
            client_secret (str): Spotify client secret

        Returns:
            SpotifyOAuth: The OAuth manager
        """
        return SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            open_browser=True,
        )

    def get_cached_token(self) -> Optional[Dict[str, Any]]:
        """
        Get a cached token if available and not expired.

        Returns:
            dict: Token information or None if not available
        """
        credentials = self.cache.load_credentials()
        if (
            not credentials
            or not credentials.get("client_id")
            or not credentials.get("client_secret")
        ):
            logger.warning("No valid credentials found")
            return None

        try:
            oauth_manager = self._create_oauth_manager(
                credentials["client_id"], credentials["client_secret"]
            )

            # Try to get cached token
            token_info = oauth_manager.get_cached_token()

            if token_info:
                # Check if token needs refresh
                if oauth_manager.is_token_expired(token_info):
                    logger.info("Token expired, refreshing...")
                    token_info = oauth_manager.refresh_access_token(
                        token_info["refresh_token"]
                    )

                return token_info
            else:
                logger.info("No cached token found, need to authenticate")
                # Get new token through authorization flow
                token_info = oauth_manager.get_access_token(as_dict=False)
                return token_info

        except Exception as e:
            logger.error(f"Error getting token: {e}")
            return None

    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh an expired access token.

        Args:
            refresh_token (str): The refresh token

        Returns:
            dict: New token information or None if failed
        """
        credentials = self.cache.load_credentials()
        if not credentials:
            return None

        try:
            oauth_manager = self._create_oauth_manager(
                credentials["client_id"], credentials["client_secret"]
            )

            return oauth_manager.refresh_access_token(refresh_token)

        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None

    # =====================
    # Client Creation Methods
    # =====================

    def create_spotify_client(self) -> Optional[spotipy.Spotify]:
        """
        Get an authenticated Spotify client.

        Returns:
            spotipy.Spotify: An authenticated Spotify client or None if failed
        """
        token_info = self.get_cached_token()

        if not token_info:
            logger.warning("No valid token available. Please run setup first.")
            return None

        try:
            spotify_client = spotipy.Spotify(auth=token_info["access_token"])
            logger.info("Spotify client created successfully")
            return spotify_client
        except Exception as e:
            logger.error(f"Error creating Spotify client: {e}")
            return None
