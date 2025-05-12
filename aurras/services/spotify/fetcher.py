from typing import Dict, Any


class SpotifyUserDataRetriever:
    def __init__(self):
        """Initialize the FetchUserData."""

    def _get_spotify_client(self):
        """Get the client from client service."""
        from aurras.services.spotify.connection import SetupSpotifyConnection

        client = SetupSpotifyConnection()
        if not client:
            return None

        return client.create_spotify_client()

    def _validate_client_exists(self):
        """Check if the client exists."""
        client = self._get_spotify_client()

        if client:
            return client

    def retrieve_current_user(self) -> Dict[str, Any]:
        """
        Get information about the current user.

        Returns:
            dict: Spotify API response with user information
        """
        if client := self._get_spotify_client():
            return client.current_user()

    def retrieve_user_playlists(self, limit: int = 50):
        """
        Get playlists from the user's Spotify account.

        Args:
            limit: Maximum number of playlists to return

        Returns:
            dict: Spotify API response with playlists
        """
        if client := self._get_spotify_client():
            return client.current_user_playlists(limit=limit)

    def retrieve_playlist_tracks(self, playlist_id: str) -> Dict[str, Any]:
        """
        Get tracks from a Spotify playlist.

        Args:
            playlist_id: The Spotify playlist ID

        Returns:
            dict: Spotify API response with tracks
        """
        if client := self._get_spotify_client():
            return client.playlist_tracks(playlist_id=playlist_id)
