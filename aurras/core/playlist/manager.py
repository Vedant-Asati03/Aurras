"""
Playlist Manager Module

This module provides a central class for managing playlists, including creating,
downloading, deleting, and modifying playlists, as well as adding and removing songs.
"""

import time
import logging
from typing import Any, List, Dict, Optional

from aurras.utils.console import console
from aurras.core.playlist.cache.updater import UpdatePlaylistDatabase
from aurras.core.playlist.cache.search_db import SearchFromPlaylistDataBase

logger = logging.getLogger(__name__)


class PlaylistManager:
    """
    Central class for managing playlists in Aurras.
    Combines functionality for creating, downloading, modifying, and deleting playlists.
    """

    def __init__(self):
        """Initialize the PlaylistManager."""
        self.db_updater = UpdatePlaylistDatabase()
        self.db_searcher = SearchFromPlaylistDataBase()

        # State management
        self.active_playlist = None
        self.active_song = None

    def create_playlist(self, playlist_name: str, description: str = "") -> None:
        """
        Create a new playlist.

        Args:
            playlist_name: Name of the playlist to create
            description: Optional description of the playlist
        """
        try:
            current_time = int(time.time())

            self.db_updater.save_playlist(
                playlist_name=playlist_name,
                description=description,
                created_at=current_time,
                updated_at=current_time,
            )

            console.print_success(f"Created playlist '{playlist_name}'")

        except Exception as e:
            logger.error(f"Error creating playlist: {e}", exc_info=True)
            console.print_error(
                f"Error: Failed to create playlist '{playlist_name}': {str(e)}"
            )

    def delete_playlist(self, playlist_name: List[str]) -> bool:
        """
        Delete a playlist.

        Args:
            playlist_name: Name of the playlist to delete. If empty, will prompt for selection.

        Returns:
            True if successful, False otherwise
        """
        try:
            if not playlist_name:
                console.print_warning("Warning: No playlist name provided.")
                return False

            self.db_updater.remove_playlist(playlist_names=playlist_name)
            return True

        except Exception as e:
            logger.error(f"Error deleting playlist: {e}", exc_info=True)
            console.print_error(
                f"Error: Failed to delete playlist '{playlist_name}': {str(e)}"
            )
            return False

    def download_playlist(
        self,
        playlist_names: Optional[List[str]] = None,
        format: Optional[str] = None,
        bitrate: Optional[str] = None,
    ) -> bool:
        """
        Download one or more playlists.

        Args:
            playlist_names: List of playlist names to download
            format: Optional format for downloaded songs
            bitrate: Optional bitrate for downloaded songs

        Returns:
            True if successful, False otherwise
        """
        if not playlist_names:
            console.print_warning(
                "Warning: No playlist names provided. Selecting from available playlists."
            )
            return False

        try:
            from aurras.core.playlist.download import DownloadPlaylist

            playlist_downloader = DownloadPlaylist()
            success = playlist_downloader.download(playlist_names, format, bitrate)

            return success

        except Exception as e:
            logger.error(f"Error downloading playlist(s): {e}", exc_info=True)
            console.print_error(f"Error: Failed to download playlist(s): {str(e)}")
            return False

    def import_playlist(self):
        """Import playlist from spotify."""
        try:
            from aurras.services.spotify.connection import SetupSpotifyConnection

            client = SetupSpotifyConnection()

            if available_playlists := client.get_user_playlists():
                return available_playlists

            console.print_success("Imported playlist from Spotify")

        except Exception as e:
            logger.error(f"Error importing playlist: {e}", exc_info=True)
            console.print_error(f"Error: Failed to import playlist: {str(e)}")

    def get_all_playlists(self) -> Dict[str, Any]:
        """
        Get all playlists from the database.

        Returns:
            dict: Dictionary with playlist name as key and list of song names as value
        """
        if playlists := self.db_searcher.initialize_playlist_metadata():
            return playlists

    def get_playlist_songs(self, playlist_name: str) -> Dict[str, List[str]]:
        """
        Get all songs from a playlist.

        Args:
            playlist_name: Name of the playlist

        Returns:
            Dict: Dictionary with song names
        """
        songs = self.db_searcher.initialize_playlist_songs_dict(playlist_name)

        if not songs:
            console.print_warning(
                f"Warning: No songs found in playlist '{playlist_name}'"
            )
            return {}

        return songs

    def get_playlist_songs_with_complete_metadata(
        self, playlist_name: str
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Get all songs from a playlist with metadata.

        Args:
            playlist_name: Name of the playlist

        Returns:
            dict: Dictionary with song metadata
        """
        songs = self.db_searcher.initialize_playlist_songs_dict_with_metadata(
            playlist_name
        )

        if not songs:
            console.print_warning(
                f"Warning: No songs found in playlist '{playlist_name}'"
            )
            return {}

        return songs

    def search_by_song_or_artist(self, query: str) -> List[str]:
        """
        Search for playlists by song name or artist name.

        Args:
            query: Search query (song name, artist name)

        Returns:
            list: List of playlists matching the query
        """
        playlists = self.db_searcher.search_for_playlists_by_name_or_artist(query)

        if not playlists:
            console.print_warning(f"Warning: No playlists found matching '{query}'")
            return []

        return playlists
