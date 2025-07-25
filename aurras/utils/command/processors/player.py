"""
Player command processor for Aurras CLI.

This module handles music playback operations.
"""

from typing import List

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.utils.decorators import with_error_handling

logger = get_logger("aurras.command.processors.player")


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
        with logger.operation_context(operation="song_playback"):
            song_name_list = self._parse_args(song_name)

            if not song_name_list:
                logger.warning(
                    "No song specified for playback",
                    extra={"operation": "song_playback"},
                )
                console.print_error("Please specify a song to play.")
                return 1

            logger.info(
                "Starting song playback",
                extra={
                    "operation": "song_playback",
                    "song_count": len(song_name_list),
                    "show_lyrics": show_lyrics,
                },
            )

            from aurras.core.player.online import SongStreamHandler

            with logger.profile_context("song_playback"):
                SongStreamHandler(song_name_list).listen_song_online(
                    show_lyrics=show_lyrics
                )

            return 0

    @with_error_handling
    def download_song(
        self,
        song_name: str,
        playlist: str = None,
        output_dir: str = None,
        format: str = None,
        bitrate: str = None,
    ) -> int:
        """Download a song or multiple songs using enhanced downloader.

        Returns:
            int: 0 for success, 1 for error
        """
        with logger.operation_context(operation="song_download"):
            song_name_list = self._parse_args(song_name)

            if not song_name_list:
                logger.warning(
                    "No song specified for download",
                    extra={"operation": "song_download"},
                )
                console.print_error("Please specify a song to download.")
                return 1

            logger.info(
                "Starting song download",
                extra={
                    "operation": "song_download",
                    "song_count": len(song_name_list),
                    "format": format,
                    "bitrate": bitrate,
                },
            )

            from aurras.core.downloader import SongDownloader

            with logger.profile_context("song_download"):
                success = SongDownloader(
                    song_name_list, playlist, output_dir, format, bitrate
                ).download_songs()

            if success:
                logger.info(
                    "Song download completed successfully",
                    extra={
                        "operation": "song_download",
                        "song_count": len(song_name_list),
                    },
                )
            else:
                logger.error(
                    "Song download failed",
                    extra={
                        "operation": "song_download",
                        "song_count": len(song_name_list),
                    },
                )

            return 0 if success else 1
