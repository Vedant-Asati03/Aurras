import spotipy
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SpotifyClientService:
    """
    Handles Spotify API client creation and operations.

    This class creates and manages authenticated Spotify API clients
    and provides methods for common API operations.
    """

    def __init__(self):
        """Initialize the SpotifyClient."""

    def create_spotify_client(self) -> Optional[spotipy.Spotify]:
        """
        Get an authenticated Spotify client.

        Returns:
            spotipy.Spotify: An authenticated Spotify client
        """
        from aurras.services.spotify.oauth_handler import SpotifyOAuthHandler

        oauth_handler = SpotifyOAuthHandler()
        credentials = oauth_handler.get_cached_token()

        if not credentials:
            return None

        token = spotipy.util.prompt_for_user_token(
            username=credentials["username"],
            scope=credentials["scope"],
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            redirect_uri=credentials["redirect_uri"],
        )

        if spotify_client := spotipy.Spotify(auth=token):
            return spotify_client
