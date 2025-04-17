"""
Playlist command processor for Aurras CLI.

This module handles playlist management and playback operations.
"""

import logging
from typing import List, Optional

from ...console.renderer import ListDisplay, get_console
from ...theme_helper import ThemeHelper, with_error_handling
from ....player.online import SongStreamHandler
from ....playlist.manager import PlaylistManager
from ....utils.handle_fuzzy_search import FuzzySearcher

logger = logging.getLogger(__name__)
console = get_console()


class PlaylistProcessor:
    """Handle playlist-related commands and operations."""

    def __init__(self):
        """Initialize the playlist processor."""
        self.playlist_manager = PlaylistManager()
        self.fuzzy_search = FuzzySearcher(threshold=0.56)

    def _parse_args(self, arg: str) -> List[str]:
        """Returns a list of songs from a comma-separated string."""
        return arg.strip("'\"").split(", ") if arg else []

    def _get_corrected_playlist_name(self, playlist_name: str) -> Optional[str | None]:
        """Returns the actual playlist name from the user query."""
        theme_styles = ThemeHelper.get_theme_colors()
        warning_color = theme_styles.get("warning", "yellow")

        available_playlists = list(self.playlist_manager.get_all_playlists().keys())

        corrected_playlist_name = self.fuzzy_search.find_best_match(
            playlist_name, available_playlists
        )

        if not corrected_playlist_name:
            console.print(
                f"[{warning_color}]Please specify a playlist to play[/{warning_color}]"
            )
            return None

        return corrected_playlist_name

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
        theme_styles = ThemeHelper.get_theme_colors()

        success_color = theme_styles.get("success", "green")
        warning_color = theme_styles.get("warning", "yellow")

        if not playlist_name:
            console.print(
                f"[{warning_color}]Please specify a playlist to play[/{warning_color}]"
            )
            return 1

        playlist_name = self._get_corrected_playlist_name(playlist_name)

        console.print(
            f"[{success_color}]Playing playlist: {playlist_name}[/{success_color}]"
        )

        try:
            song_name_list = self.playlist_manager.get_playlist_songs(playlist_name)

            if not song_name_list:
                console.print(
                    f"[{warning_color}]Playlist '{playlist_name}' not found or empty[/{warning_color}]"
                )
                return 1

            logger.info(
                f"Playlist {playlist_name} with songs: '{', '.join(song_name_list)}'"
            )
            SongStreamHandler(song_name_list).listen_song_online(
                show_lyrics=show_lyrics, shuffle=shuffle
            )
            return 0

        except Exception as e:
            logger.error(f"Error playing playlist: {e}", exc_info=True)
            console.print(f"[red]Error playing playlist:[/red] {str(e)}")
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
        playlist_to_download: List[str] = []

        theme_styles = ThemeHelper.get_theme_colors()

        success_color = theme_styles.get("success", "green")
        warning_color = theme_styles.get("warning", "yellow")

        if not playlist_names:
            console.print(
                f"[{warning_color}]Error: No playlist name provided[/{warning_color}]"
            )
            return 1

        listed_playlist_names = self._parse_args(playlist_names)

        if not listed_playlist_names:
            console.print(
                f"[{warning_color}]Error: No playlist names provided[/{warning_color}]"
            )
            return 1

        for playlist_name in listed_playlist_names:
            playlist_to_download.append(
                self._get_corrected_playlist_name(playlist_name)
            )

        console.print(
            f"[{success_color}]Downloading playlists: {', '.join(playlist_to_download)}[/{success_color}]"
        )
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
        theme_styles = ThemeHelper.get_theme_colors()

        warning_color = theme_styles.get("warning", "yellow")

        if not playlist_name:
            console.print(
                f"[{warning_color}]Error: No playlist name provided[/{warning_color}]"
            )
            return 1

        playlist_name = self._get_corrected_playlist_name(playlist_name)

        playlist_songs = self.playlist_manager.get_playlist_songs(playlist_name)

        if not playlist_songs:
            console.print(
                f"[{warning_color}]Playlist '{playlist_name}' not found or empty[/{warning_color}]"
            )
            return 1

        list_display = ListDisplay(
            items=playlist_songs,
            title=f"Contents of Playlist: {playlist_name}",
            use_table=True,
            style_key="playlist",
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
        theme_styles = ThemeHelper.get_theme_colors()

        warning_color = theme_styles.get("warning", "yellow")

        available_playlists = list(self.playlist_manager.get_all_playlists().keys())

        if not available_playlists:
            console.print(
                f"[{warning_color}]No playlists available. Please create a playlist.[/{warning_color}]"
            )
            return 1

        playlist_names = self._get_corrected_playlist_name(available_playlists)

        if not playlist_names:
            console.print(
                f"[{warning_color}]No matching playlists found[/{warning_color}]"
            )
            return 1

        list_display = ListDisplay(
            items=playlist_names,
            title="Available Playlists",
            use_table=True,
            style_key="playlist",
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

        theme_styles = ThemeHelper.get_theme_colors()

        success_color = theme_styles.get("success", "green")
        warning_color = theme_styles.get("warning", "yellow")

        if not playlist_names:
            console.print(
                f"[{warning_color}]Error: No playlist name provided[/{warning_color}]"
            )
            return 1

        listed_playlist_names = self._parse_args(playlist_names)

        for playlist_name in listed_playlist_names:
            playlist_to_delete.append(self._get_corrected_playlist_name(playlist_name))

        if not playlist_to_delete:
            console.print(
                f"[{warning_color}]Error: No matching playlists found[/{warning_color}]"
            )
            return 1

        self.playlist_manager.delete_playlist(playlist_to_delete)

        console.print(
            f"[{success_color}]Deleted playlists: {', '.join(playlist_to_delete)}[/{success_color}]"
        )
        return 0

    def import_playlist(self, source=None, playlist_id=None):
        """
        Import a playlist from an external source like Spotify.

        Args:
            source: Source name (e.g., "spotify")
            playlist_id: Playlist ID or URL

        Returns:
            int: 0 for success, 1 for failure
        """
        if not source or not playlist_id:
            console.print("[yellow]Error: Source and playlist ID are required[/yellow]")
            return 1

        try:
            # This would be connected to the actual import functionality
            # Future enhancement: Implement proper playlist import
            console.print(
                f"[yellow]Feature not yet implemented: importing playlist from {source}[/yellow]"
            )
            return 0
        except Exception as e:
            logger.error(f"Error importing playlist: {e}", exc_info=True)
            console.print(f"[red]Error importing playlist:[/red] {str(e)}")
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
        theme_styles = ThemeHelper.get_theme_colors()

        warning_color = theme_styles.get("warning", "yellow")

        if not query:
            console.print(
                f"[{warning_color}]Error: No search query provided[/{warning_color}]"
            )
            return 1

        playlist_names = list(self.playlist_manager.search_by_song_or_artist(query).keys())

        if not playlist_names:
            console.print(
                f"[{warning_color}]No matching playlists found for '{query}'[/{warning_color}]"
            )
            return 1

        list_display = ListDisplay(
            items=playlist_names,
            title=f"Playlists containing '{query}'",
            use_table=True,
            style_key="playlist",
        )

        console.print(list_display.render())
        return 0


# Instantiate processor for direct import
processor = PlaylistProcessor()
