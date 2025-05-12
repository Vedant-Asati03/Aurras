"""
This Module provides functionality for downloading one or more playlists.
"""

import logging
from typing import List, Dict, Optional

from aurras.utils.console import console
from aurras.core.playlist.cache.search_db import SearchFromPlaylistDataBase

logger = logging.getLogger(__name__)


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
            if self._check_if_already_downloaded(playlist):
                console.print_error("Error: Playlist already downloaded")
                continue

            try:
                songs_data = self._retrieve_playlist_songs(playlist)

                if not songs_data:
                    console.print_error(
                        f"Error: No songs found in playlist '{playlist}'"
                    )
                    continue

                song_names = [song["track_name"] for song in songs_data]

                self._download_songs(song_names, playlist, format, bitrate)

                console.print_success(
                    f"Success: Playlist '{playlist}' downloaded and saved"
                )

            except Exception as e:
                logger.error(
                    f"Error downloading playlist '{playlist}': {e}", exc_info=True
                )
                console.print_error(
                    f"Error: Failed to download playlist '{playlist}': {str(e)}"
                )
                return False

        return True

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

    def _retrieve_playlist_songs(self, playlist: str) -> List[Dict[str, str]]:
        """
        Fetch the list of songs from a playlist using the SearchFromPlaylistDataBase.

        Args:
            playlist_name: Name of the playlist to fetch

        Returns:
            List of song dictionaries with metadata
        """
        try:
            playlist_data = self.search_db.initialize_playlist_songs_dict_with_metadata(
                playlist
            )

            if playlist in playlist_data and playlist_data[playlist]:
                logger.info(
                    f"Found {len(playlist_data[playlist])} songs in playlist '{playlist}'"
                )
                return playlist_data[playlist]

            logger.info(f"No songs found in playlist '{playlist}' in database")

            return []

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
    ) -> None:
        """
        Download songs using the SongDownloader.

        Args:
            songs: List of song names
            output_dir: Directory to save downloaded songs
            format: Optional format for downloaded songs
            bitrate: Optional bitrate for downloaded songs
        """
        from aurras.utils.command.processors.player import processor

        processor.download_song(
            song_name=songs, playlist=playlist, format=format, bitrate=bitrate
        )
