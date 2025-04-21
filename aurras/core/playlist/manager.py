"""
Playlist Manager Module

This module provides a central class for managing playlists, including creating,
downloading, deleting, and modifying playlists, as well as adding and removing songs.
"""

import time
import logging
from typing import List, Dict, Optional

from .download import DownloadPlaylist
from .cache.updater import UpdatePlaylistDatabase
from .cache.search_db import SearchFromPlaylistDataBase
from ..downloader import ThemeHelper
from ...utils.console.manager import get_console

logger = logging.getLogger(__name__)

console = get_console()


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

        _, self.theme_styles = ThemeHelper.retrieve_theme_gradients_and_styles()

    def get_theme_color(self, key: str, default: str) -> str:
        """Get a color from the current theme."""
        return ThemeHelper.get_theme_color(self.theme_styles, key, default)

    def create_playlist(self, playlist_name: str, description: str = "") -> None:
        """
        Create a new playlist.

        Args:
            playlist_name: Name of the playlist to create
            description: Optional description of the playlist
        """
        success_color = self.get_theme_color("success", "green")
        error_color = self.get_theme_color("error", "red")

        try:
            current_time = int(time.time())

            self.db_updater.save_playlist(
                playlist_name=playlist_name,
                description=description,
                created_at=current_time,
                updated_at=current_time,
            )

            console.print(
                f"[bold {success_color}]Success:[/] Created playlist '{playlist_name}'"
            )

        except Exception as e:
            logger.error(f"Error creating playlist: {e}", exc_info=True)
            console.print(
                f"[bold {error_color}]Error:[/] Failed to create playlist: {str(e)}"
            )

    def delete_playlist(self, playlist_name: List[str]) -> bool:
        """
        Delete a playlist.

        Args:
            playlist_name: Name of the playlist to delete. If empty, will prompt for selection.

        Returns:
            True if successful, False otherwise
        """
        success_color = self.get_theme_color("success", "green")
        error_color = self.get_theme_color("error", "red")
        info_color = self.get_theme_color("info", "blue")

        try:
            if not playlist_name:
                console.print(
                    f"[bold {info_color}]Warning:[/] No playlist name provided. Selecting from available playlists."
                )
                return False

            self.db_updater.remove_playlist(playlist_names=playlist_name)

            console.print(
                f"[bold {success_color}]Success:[/] Deleted playlist '{', '.join(playlist_name)}'"
            )

            return True

        except Exception as e:
            logger.error(f"Error deleting playlist: {e}", exc_info=True)
            console.print(
                f"[bold {error_color}]Error:[/] Failed to delete playlist: {str(e)}"
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
        error_color = self.get_theme_color("error", "red")
        info_color = self.get_theme_color("info", "blue")

        if not playlist_names:
            console.print(
                f"[bold {info_color}]Warning:[/] No playlist names provided. Selecting from available playlists."
            )
            return False

        try:
            playlist_downloader = DownloadPlaylist(playlist_names)
            success = playlist_downloader.download(format, bitrate)

            return success

        except Exception as e:
            logger.error(f"Error downloading playlist(s): {e}", exc_info=True)
            console.print(
                f"[bold {error_color}]Error:[/] Failed to download playlist(s): {str(e)}"
            )
            return False

    def get_all_playlists(self) -> Dict[str, List[str]]:
        """
        Get all playlists from the database.

        Returns:
            dict: Dictionary with playlist name as key and list of song names as value
        """
        playlists = self.db_searcher.initialize_playlist_dict()

        if not playlists:
            return {}

        return playlists

    def get_playlist_songs(self, playlist_name: str) -> List[str]:
        """
        Get all songs from a playlist.

        Args:
            playlist_name: Name of the playlist

        Returns:
            List of songs in the playlist
        """
        songs = self.db_searcher.initialize_playlist_songs_dict(playlist_name).get(playlist_name, "")

        if not songs:
            warning_color = self.get_theme_color("warning", "yellow")
            console.print(
                f"[{warning_color}]No songs found in playlist '{playlist_name}'[/]"
            )
            return []

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
            warning_color = self.get_theme_color("warning", "yellow")
            console.print(
                f"[{warning_color}]No songs found in playlist '{playlist_name}'[/]"
            )
            return {}

        return songs

    def search_by_song_or_artist(self, query: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Search for playlists by song name or artist name.

        Args:
            query: Search query (song name, artist name)

        Returns:
            dict: Dictionary with playlist name as key and list of song metadata as value
        """
        playlists_with_metadata = (
            self.db_searcher.search_for_playlists_by_name_or_artist(query)
        )

        if not playlists_with_metadata:
            warning_color = self.get_theme_color("warning", "yellow")
            console.print(f"[{warning_color}]No playlists found matching '{query}'[/]")
            return {}

        return playlists_with_metadata
