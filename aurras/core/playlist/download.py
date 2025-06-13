"""
This Module provides functionality for downloading one or more playlists.
"""

from itertools import chain
from typing import List, Optional

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.core.playlist.cache.search_db import SearchFromPlaylistDataBase

logger = get_logger("aurras.core.playlist.download", log_to_console=False)


class DownloadPlaylist:
    """
    Class for downloading playlists.
    """

    def __init__(self) -> None:
        """Initialize the DownloadPlaylist class."""
        self.search_db = SearchFromPlaylistDataBase()

    def download(
        self,
        playlists: List[str],
        format: Optional[str] = None,
        bitrate: Optional[str] = None,
    ) -> bool:
        """
        Download all songs from the specified playlists.

        Args:
            format: Optional format for downloaded songs (mp3, flac, etc.)
            bitrate: Optional bitrate for downloaded songs (128k, 320k, etc.)

        Returns:
            bool: True if download was successful, False otherwise
        """
        if not playlists:
            console.print_error("Error: No playlists specified for download")
            return False

        console.print_success(f"Downloading playlist: {', '.join(playlists)}")

        for playlist in playlists:
            if not self._check_if_playlist_exists(playlist):
                console.print_error(f"Error: Playlist '{playlist}' does not exist")
                console.print_info(
                    "Try running: `aurras playlist --list` to see available playlists."
                )
                continue

            if self._check_if_already_downloaded(playlist):
                console.print_info("Playlist already downloaded!")
                continue

            try:
                song_names = self._retrieve_playlist_songs(playlist)

                if not song_names:
                    console.print_error(
                        f"Error: No songs found in playlist '{playlist}'"
                    )
                    continue

                download_success = self._download_songs(
                    song_names, playlist, format, bitrate
                )

                if download_success:
                    # Mark playlist as downloaded only after successful download
                    from aurras.core.playlist.cache.updater import (
                        UpdatePlaylistDatabase,
                    )

                    db_updater = UpdatePlaylistDatabase()
                    db_updater.mark_playlist_as_downloaded(playlist)

                    console.print_success(
                        f"Success: Playlist '{playlist}' downloaded and saved"
                    )
                else:
                    console.print_error(
                        f"Error: Playlist '{playlist}' download failed or completed with errors"
                    )
                    logger.warning(
                        f"Playlist '{playlist}' download failed - not marking as downloaded"
                    )
                    return False

            except Exception as e:
                logger.error(
                    f"Error downloading playlist '{playlist}': {e}", exc_info=True
                )
                console.print_error(
                    f"Error: Failed to download playlist '{playlist}': {str(e)}"
                )
                return False

        return True

    def _check_if_playlist_exists(self, playlist: str) -> bool:
        """
        Check if the playlist exists in the database.

        Args:
            playlist: Name of the playlist to check

        Returns:
            bool: True if the playlist exists, False otherwise
        """
        try:
            return self.search_db.check_if_playlist_exists(playlist)

        except Exception as e:
            logger.error(f"Error checking if playlist exists: {e}", exc_info=True)
            console.print(f"[red]Error checking playlist existence: {str(e)}[/red]")
            return False

    def _check_if_already_downloaded(self, playlist: str) -> bool:
        """
        Check if the playlist is already downloaded.

        Args:
            playlist: Name of the playlist to check

        Returns:
            bool: True if already downloaded, False otherwise
        """
        try:
            return self.search_db.check_if_playlist_is_downloaded(playlist)

        except Exception as e:
            logger.error(
                f"Error checking if playlist is downloaded: {e}", exc_info=True
            )
            console.print(f"[red]Error checking playlist status: {str(e)}[/red]")
            return False

    def _retrieve_playlist_songs(self, playlist: str) -> List[str]:
        """
        Fetch the list of songs from a playlist using the SearchFromPlaylistDataBase.

        Args:
            playlist_name: Name of the playlist to fetch

        Returns:
            List of song dictionaries with metadata
        """
        try:
            if playlist:
                playlist_metadata = self.search_db.create_playlist_tracks_dict(playlist)
            else:
                playlist_metadata = self.search_db.create_playlist_tracks_dict()

            if not playlist_metadata:
                console.print_warning(
                    f"Warning: No songs found in playlist '{playlist}'"
                )
                return []

            playlist_songs = [
                song["track_name"]
                for song in chain.from_iterable(playlist_metadata.values())
            ]

            if not playlist_songs:
                logger.info(f"No songs found in playlist '{playlist}' in database")
                return []

            return playlist_songs

        except Exception as e:
            logger.error(f"Error fetching playlist songs: {e}", exc_info=True)
            console.print(f"[red]Error fetching songs from playlist: {str(e)}[/red]")
            return []

    def _download_songs(
        self,
        songs: List[str],
        playlist: str,
        format: Optional[str],
        bitrate: Optional[str],
    ) -> bool:
        """
        Download songs using the SongDownloader.

        Args:
            songs: List of song names
            playlist: Name of the playlist (for organizing downloads)
            format: Optional format for downloaded songs
            bitrate: Optional bitrate for downloaded songs

        Returns:
            bool: True if download was successful, False otherwise
        """
        from aurras.utils.command.processors import player_processor

        # Convert list of songs to comma-separated string format expected by player_processor
        songs_str = ", ".join(songs) if songs else ""

        result = player_processor.download_song(
            song_name=songs_str, playlist=playlist, format=format, bitrate=bitrate
        )

        return result == 0
