"""
Spotify Client Module

This module handles Spotify API client creation and interactions.
"""

from aurras.utils.logger import get_logger

logger = get_logger("aurras.services.spotify.connection", log_to_console=False)

SCOPE = "playlist-read-private"
REDIRECT_URI = "https://localhost:8080/"


class SetupSpotifyConnection:
    """
    Handles Spotify API client creation and operations.

    This class creates and manages authenticated Spotify API clients
    and provides methods for common API operations.
    """

    def __init__(self):
        """Initialize the SpotifyClient."""

    def create_spotify_client(self):
        """
        Get an authenticated Spotify client.

        Returns:
            spotipy.Spotify: An authenticated Spotify client
        """
        from aurras.services.spotify.cache import CredentialsCache

        cache = CredentialsCache()
        credentials = cache.load_credentials()

        if not credentials:
            return None

        import spotipy

        token = spotipy.util.prompt_for_user_token(
            username=credentials["username"],
            scope=SCOPE,
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            redirect_uri=REDIRECT_URI,
        )

        if spotify_client := spotipy.Spotify(auth=token):
            return spotify_client
