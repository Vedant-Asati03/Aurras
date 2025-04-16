"""
Player command processor for Aurras CLI.

This module handles music playback operations.
"""

import logging
from typing import List

from ...console.manager import get_console
from ....core.downloader import SongDownloader
from ....player.online import SongStreamHandler
from ...theme_helper import ThemeHelper, with_error_handling

logger = logging.getLogger(__name__)
console = get_console()


class PlayerProcessor:
    """Handle music player operations."""

    def __init__(self):
        """Initialize the player processor."""
        pass

    def _parse_args(self, arg: str) -> List[str]:
        """Returns a list of songs from a comma-separated string."""
        return arg.strip("'\"").split(", ") if arg else []

    @with_error_handling
    def play_song(self, song_name: str, show_lyrics=True):
        """Play a song or multiple songs."""
        song_name_list = self._parse_args(song_name)

        if song_name_list:
            logger.info(f"Command-line song argument: '{', '.join(song_name_list)}'")
            SongStreamHandler(song_name_list).listen_song_online(
                show_lyrics=show_lyrics
            )
            return 0
        else:
            theme_styles = ThemeHelper.get_theme_colors()
            warning_color = theme_styles.get("warning", "yellow")
            console.print(
                f"[{warning_color}]Please specify a song to play.[/{warning_color}]"
            )
            return 1

    @with_error_handling
    def download_song(self, song_name, output_dir=None, format=None, bitrate=None):
        """Download a song or multiple songs using enhanced downloader."""
        song_name_list = self._parse_args(song_name)

        if not song_name_list:
            theme_styles = ThemeHelper.get_theme_colors()
            warning_color = theme_styles.get("warning", "yellow")
            console.print(
                f"[{warning_color}]Please specify a song to download.[/{warning_color}]"
            )
            return 1

        SongDownloader(song_name_list, output_dir, format, bitrate).download_songs()
        return 0


# Instantiate processor for direct import
processor = PlayerProcessor()
