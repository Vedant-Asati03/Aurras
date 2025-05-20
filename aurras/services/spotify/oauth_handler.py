"""
Spotify Authentication Module

This module handles Spotify API authentication, including credential management,
OAuth token handling, and related functionality.
"""

from typing import Dict, Optional, Any
from aurras.utils.logger import get_logger

logger = get_logger("aurras.services.spotify.oauth_handler", log_to_console=False)

SCOPE = "playlist-read-private"
REDIRECT_URI = "https://localhost:8080/"


class SpotifyOAuthHandler:
    """
    Handles Spotify API authentication and credential management.

    This class provides methods for managing Spotify API credentials,
    obtaining and refreshing OAuth tokens, and creating authenticated clients.
    """

    def __init__(self):
        """Initialize the SpotifyAuth."""

    def _create_oauth_manager(self, client_id: str, client_secret: str):
        """
        Create a SpotifyOAuth manager.

        Args:
            client_id (str): Spotify client ID
            client_secret (str): Spotify client secret

        Returns:
            SpotifyOAuth: The OAuth manager
        """
        from spotipy.oauth2 import SpotifyOAuth

        return SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            open_browser=True,
        )

    def get_cached_token(self, credentials: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Get a cached token if available and not expired.

        Args:
            credentials (dict): Dictionary with client_id and client_secret

        Returns:
            dict: Token info if valid cached token exists, None otherwise
        """
        try:
            auth = self._create_oauth_manager(
                credentials["client_id"], credentials["client_secret"]
            )
            token_info = auth.get_access_token()

            if auth.is_token_expired(token_info):
                token_info = self._refresh_expired_token(
                    auth, token_info["refresh_token"]
                )

            if token_info:
                return token_info
            return None

        except Exception as e:
            logger.warning(f"Error getting cached token: {e}")
            return None

    def _refresh_expired_token(
        self, auth, refresh_token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Refresh an expired token using the refresh token.

        Args:
            token_info (dict): The current token info
            refresh_token (str): The refresh token

        Returns:
            dict: New token info if successful, None otherwise
        """
        try:
            new_token_info = auth.refresh_access_token(refresh_token)
            logger.info("Token refreshed successfully.")
            return new_token_info

        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None

    def ensure_valid_redirect_url(self, redirect_url: str) -> None:
        """
        Validate the redirect URL format.

        Args:
            redirect_url (str): The URL to validate

        Raises:
            ValueError: If the URL format is invalid
        """
        if not redirect_url:
            raise ValueError("Authentication cancelled")

        if redirect_url.startswith("https://accounts.spotify.com"):
            raise ValueError(
                "Incorrect URL provided - need redirect URL, not original authorization URL"
            )

        if not redirect_url.startswith("http://localhost:8080"):
            raise ValueError("Invalid redirect URL format")
