"""
Spotify Service Main Module

This module provides a unified interface for all Spotify functionality.
"""

from typing import Dict, Any, Optional, List, Callable
from aurras.utils.logger import get_logger
from aurras.utils.console import console

logger = get_logger("aurras.services.spotify.service", log_to_console=False)


class SpotifyService:
    """
    Main Spotify service class that provides a unified interface
    for all Spotify functionality including setup, authentication,
    and data retrieval.
    """

    def __init__(self):
        """Initialize the Spotify service."""
        self._setup = None
        self._client_service = None
        self._fetcher = None
        self._cache = None

    @property
    def setup(self):
        """Get the setup service."""
        if self._setup is None:
            from .auth import SpotifyAuth

            self._setup = SpotifyAuth()
        return self._setup

    @property
    def client_service(self):
        """Get the client service."""
        if self._client_service is None:
            from .auth import SpotifyAuth

            self._client_service = SpotifyAuth()
        return self._client_service

    @property
    def fetcher(self):
        """Get the data fetcher."""
        if self._fetcher is None:
            from .api import SpotifyDataRetriever

            self._fetcher = SpotifyDataRetriever()
        return self._fetcher

    @property
    def cache(self):
        """Get the credentials cache."""
        if self._cache is None:
            from .cache import SpotifyCredentialsCache

            self._cache = SpotifyCredentialsCache()
        return self._cache

    def is_setup(self) -> bool:
        """
        Check if Spotify credentials are properly set up.

        Returns:
            bool: True if credentials exist and are valid
        """
        try:
            return self.cache.is_setup()
        except Exception as e:
            logger.error(f"Error checking setup status: {e}")
            return False

    def setup_credentials(self) -> bool:
        """
        Run the setup process for Spotify credentials.

        Returns:
            bool: True if setup was successful
        """
        return self.setup.setup_credentials()

    def get_authenticated_client(self):
        """
        Get an authenticated Spotify client.

        Returns:
            spotipy.Spotify: Authenticated client or None if failed
        """
        if not self.is_setup():
            console.print_error("Spotify not set up. Please run setup first.")
            return None

        return self.client_service.create_spotify_client()

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current user information.

        Returns:
            dict: User information or None if failed
        """
        try:
            return self.fetcher.retrieve_current_user()
        except Exception as e:
            logger.error(f"Error retrieving user info: {e}")
            return None

    def get_user_playlists(
        self, limit: int = 50, progress_callback: Optional[Callable] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's playlists.

        Args:
            limit: Maximum number of playlists to return
            progress_callback: Optional callback function for progress updates

        Returns:
            dict: Playlists data or None if failed
        """
        try:
            return self.fetcher.retrieve_user_playlists(
                limit=limit, progress_callback=progress_callback
            )
        except Exception as e:
            logger.error(f"Error retrieving playlists: {e}")
            return None

    def get_playlist_tracks(
        self, playlist_id: str, progress_callback: Optional[Callable] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get tracks from a specific playlist.

        Args:
            playlist_id: The Spotify playlist ID
            progress_callback: Optional callback function for progress updates

        Returns:
            dict: Playlist tracks data or None if failed
        """
        try:
            return self.fetcher.retrieve_playlist_tracks(
                playlist_id, progress_callback=progress_callback
            )
        except Exception as e:
            logger.error(f"Error retrieving playlist tracks: {e}")
            return None

    def import_playlists(
        self, progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Import all playlists from the user's Spotify account and save them to the database.

        Args:
            progress_callback: Optional callback function for progress updates

        Returns:
            list: List of imported playlists with their tracks
        """
        imported_playlists = []

        try:
            if progress_callback:
                progress_callback("Fetching playlists from Spotify...")

            playlists_data = self.get_user_playlists(
                progress_callback=progress_callback
            )
            if not playlists_data:
                console.print_error("Failed to retrieve playlists")
                return imported_playlists

            playlists = playlists_data.get("items", [])
            console.print_info(f"Found {len(playlists)} playlists to import")

            from aurras.core.playlist.cache.updater import UpdatePlaylistDatabase

            db_updater = UpdatePlaylistDatabase()

            import time

            current_time = int(time.time())

            for i, playlist in enumerate(playlists):
                playlist_id = playlist["id"]
                playlist_name = playlist["name"]

                if progress_callback:
                    progress_callback(
                        f"Importing playlist: {playlist_name} ({i + 1}/{len(playlists)})"
                    )

                console.print_info(f"Importing playlist: {playlist_name}")

                # Get tracks for this playlist
                tracks_data = self.get_playlist_tracks(
                    playlist_id, progress_callback=progress_callback
                )
                if tracks_data:
                    tracks = tracks_data.get("items", [])

                    # Save playlist to database
                    playlist_description = playlist.get(
                        "description", "Imported from Spotify"
                    )
                    db_updater.save_playlist(
                        playlist_name=playlist_name,
                        description=playlist_description,
                        updated_at=current_time,
                        is_downloaded=False,
                    )

                    # Prepare track metadata for batch save
                    songs_metadata = []
                    for track_item in tracks:
                        track = track_item.get("track")
                        if track and track.get("name"):  # Skip null tracks
                            track_name = track["name"]
                            artist_names = [
                                artist["name"] for artist in track.get("artists", [])
                            ]
                            artist_name = (
                                ", ".join(artist_names)
                                if artist_names
                                else "Unknown Artist"
                            )

                            # Format for batch_save_songs_to_playlist: (track_name, artist_name, ?, ?, added_at)
                            # The method expects 5 elements and accesses data[4] for added_at
                            songs_metadata.append(
                                (
                                    track_name,  # data[0]
                                    artist_name,  # data[1]
                                    "",  # data[2] - placeholder
                                    "",  # data[3] - placeholder
                                    current_time,  # data[4] - added_at
                                )
                            )

                    # Save tracks to database if we have any
                    if songs_metadata:
                        db_updater.batch_save_songs_to_playlist(
                            playlist_name, songs_metadata
                        )

                    playlist_info = {
                        "id": playlist_id,
                        "name": playlist_name,
                        "description": playlist_description,
                        "tracks_total": len(tracks),
                        "tracks": tracks,
                    }
                    imported_playlists.append(playlist_info)
                    console.print_success(
                        f"✓ Imported {playlist_name} ({len(songs_metadata)} tracks)"
                    )
                else:
                    console.print_warning(
                        f"Failed to import tracks for {playlist_name}"
                    )

            console.print_success(
                f"Successfully imported {len(imported_playlists)} playlists to database"
            )
            return imported_playlists

        except Exception as e:
            logger.error(f"Error importing playlists: {e}")
            console.print_error(f"Error importing playlists: {e}")
            return imported_playlists

    def reset_credentials(self) -> bool:
        """
        Reset stored Spotify credentials.

        Returns:
            bool: True if reset was successful
        """
        try:
            success = self.cache.reset_credentials()

            if success:
                console.print_success(" Spotify credentials have been reset")
                console.print_info(
                    "Run 'aurras setup --spotify' to reconfigure Spotify integration"
                )
            else:
                console.print_error(" Failed to reset Spotify credentials")

            return success

        except Exception as e:
            logger.error(f"Error resetting credentials: {e}")
            console.print_error(f"Error resetting credentials: {e}")
            return False
