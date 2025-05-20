"""
Playlist command processor for Aurras CLI.

This module handles playlist management and playback operations.
"""

from typing import List

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.utils.decorators import with_error_handling
from aurras.core.playlist.manager import PlaylistManager
from aurras.utils.handle_fuzzy_search import FuzzySearcher

logger = get_logger("aurras.command.processors.playlist", log_to_console=False)


class PlaylistProcessor:
    """Handle playlist-related commands and operations."""

    def __init__(self):
        """Initialize the playlist processor."""
        self.playlist_manager = PlaylistManager()
        self.fuzzy_search = FuzzySearcher(threshold=0.56)

    def _parse_args(self, arg: str) -> List[str]:
        """Returns a list of songs from a comma-separated string."""
        return arg.strip("'\"").split(", ") if arg else []

    @with_error_handling
    def play_playlist(self, playlist_name: str, show_lyrics=True, shuffle=False):
        """
        Play a playlist with the given options.

        Args:
            playlist_name: Name of the playlist to play
            show_lyrics: Whether to display lyrics during playback
            shuffle: Whether to shuffle the playlist
            repeat: Whether to repeat the playlist

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        if not playlist_name:
            console.print_error("Please specify a playlist to play.")
            return 1

        console.print_success(f"Playing playlist: {playlist_name}")

        try:
            playlist_songs = self.playlist_manager.get_playlist_songs(playlist_name)

            if not playlist_songs:
                console.print_error(f"Playlist '{playlist_name}' not found or empty")
                return 1

            from ....core.player.online import SongStreamHandler

            SongStreamHandler(list(playlist_songs)).listen_song_online(
                show_lyrics=show_lyrics, shuffle=shuffle
            )
            return 0

        except Exception as e:
            logger.error(f"Error playing playlist: {e}", exc_info=True)
            console.print_error(f"Error playling playlist: {str(e)}")
            return 1

    @with_error_handling
    def download_playlist(self, playlist_names: str, format=None, bitrate=None):
        """
        Download a playlist or multiple playlists.

        Args:
            playlist_names: Comma-separated list of playlist names
            format: Audio format to use for downloaded songs
            bitrate: Bitrate to use for downloaded songs

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        if not playlist_names:
            console.print_error("Please specify a playlist to download.")
            return 1

        listed_playlist_names = self._parse_args(playlist_names)

        if not listed_playlist_names:
            console.print_error("Please specify a playlist to download.")
            return 1

        playlist_to_download: List[str] = [
            self._get_corrected_playlist_name(playlist_name)
            for playlist_name in listed_playlist_names
        ]

        success = self.playlist_manager.download_playlist(
            playlist_names=playlist_to_download, format=format, bitrate=bitrate
        )

        return 0 if success else 1

    @with_error_handling
    def view_playlist(self, playlist_name: str):
        """
        View the contents of a playlist.
        Args:
            playlist_name: Name of the playlist to view
        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        if not playlist_name:
            console.print_error("Please specify a playlist to view.")
            return 1

        playlist_name = self._get_corrected_playlist_name(playlist_name)

        playlist_songs = self.playlist_manager.get_playlist_songs(playlist_name)

        if not playlist_songs:
            console.print_error(f"Playlist '{playlist_name}' not found or empty")
            return 1

        from aurras.utils.console.renderer import ListDisplay

        list_display = ListDisplay(
            items=playlist_songs,
            title=f"{playlist_name}  SONGS󰽱",
            use_table=True,
            style_key="playlist",
            show_header=False,
        )

        console.print(list_display.render())
        return 0

    @with_error_handling
    def list_playlists(self):
        """
        List all available playlists.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        available_playlists_with_metadata = self.playlist_manager.get_all_playlists()

        available_playlists_with_description = [
            (playlist["name"], playlist["description"])
            for playlist in available_playlists_with_metadata
        ]

        if not available_playlists_with_description:
            console.print_error("No playlists available. Please create a playlist.")
            return 1

        from aurras.utils.console.renderer import ListDisplay

        list_display = ListDisplay(
            items=available_playlists_with_description,
            use_table=True,
            style_key="playlist",
            show_indices=True,
        )

        console.print(list_display.render())
        return 0

    @with_error_handling
    def delete_playlist(self, playlist_names: str):
        """
        Delete a playlist.

        Args:
            playlist_name: Name of the playlist to delete

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        playlist_to_delete: List[str] = []
        listed_playlist_names = self._parse_args(playlist_names)

        for playlist_name in listed_playlist_names:
            playlist_to_delete.append(self._get_corrected_playlist_name(playlist_name))

        if not playlist_to_delete:
            console.print_error("No matching playlists found.")
            return 1

        if self.playlist_manager.delete_playlist(playlist_to_delete):
            console.print_success(f"Deleted playlists: {', '.join(playlist_to_delete)}")
            return 0

        return 1

    @with_error_handling
    def search_playlists(self, query):
        """
        Search for playlists containing specified songs or artists.

        Args:
            query: Search query (song name, artist name)

        Returns:
            int: 0 for success, 1 for failure
        """
        if not query:
            console.print_warning("No search query provided.")
            return 1

        playlist_names = self.playlist_manager.search_by_song_or_artist(query)

        from aurras.utils.console.renderer import ListDisplay

        list_display = ListDisplay(
            items=playlist_names,
            title=f"Found playlist consisting query  {query}",
            use_table=False,
            style_key="playlist",
            show_header=False,
        )

        console.print(list_display.render())
        return 0
