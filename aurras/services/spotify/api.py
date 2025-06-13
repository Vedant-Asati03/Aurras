"""
Spotify API Data Retrieval Module

This module handles all Spotify API data retrieval operations.
"""

from typing import Dict, Any, Optional, Callable


class SpotifyDataRetriever:
    """
    Handles Spotify API data retrieval operations.

    This class provides methods for fetching user data, playlists,
    and track information from the Spotify API.
    """

    def __init__(self):
        """Initialize the SpotifyDataRetriever."""

    def _get_spotify_client(self):
        """Get an authenticated Spotify client."""
        from .auth import SpotifyAuth

        auth = SpotifyAuth()
        return auth.create_spotify_client()

    def _validate_client_exists(self):
        """Check if the client exists."""
        client = self._get_spotify_client()
        return client if client else None

    def retrieve_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current user.

        Returns:
            dict: Spotify API response with user information or None if failed
        """
        client = self._get_spotify_client()
        if client:
            try:
                return client.current_user()
            except Exception as e:
                from aurras.utils.logger import get_logger

                logger = get_logger("aurras.services.spotify.api")
                logger.error(f"Error retrieving current user: {e}")
                return None
        return None

    def retrieve_user_playlists(
        self, limit: int = 50, progress_callback: Optional[Callable] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get playlists from the user's Spotify account.

        Args:
            limit: Maximum number of playlists to return
            progress_callback: Optional callback function for progress updates

        Returns:
            dict: Spotify API response with playlists or None if failed
        """
        client = self._get_spotify_client()
        if client:
            try:
                if progress_callback:
                    progress_callback("Fetching playlists from Spotify...")
                return client.current_user_playlists(limit=limit)
            except Exception as e:
                from aurras.utils.logger import get_logger

                logger = get_logger("aurras.services.spotify.api")
                logger.error(f"Error retrieving user playlists: {e}")
                return None
        return None

    def retrieve_playlist_tracks(
        self, playlist_id: str, progress_callback: Optional[Callable] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get tracks from a specific playlist.

        Args:
            playlist_id: The Spotify playlist ID
            progress_callback: Optional callback function for progress updates

        Returns:
            dict: Spotify API response with playlist tracks or None if failed
        """
        client = self._get_spotify_client()
        if client:
            try:
                if progress_callback:
                    progress_callback(f"Fetching tracks from playlist {playlist_id}...")

                # Get all tracks using pagination
                results = client.playlist_tracks(playlist_id)
                tracks = results["items"]

                # Handle pagination
                while results["next"]:
                    results = client.next(results)
                    tracks.extend(results["items"])

                return {"items": tracks}
            except Exception as e:
                from aurras.utils.logger import get_logger

                logger = get_logger("aurras.services.spotify.api")
                logger.error(f"Error retrieving playlist tracks: {e}")
                return None
        return None
