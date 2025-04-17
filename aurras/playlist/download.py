"""
This Module provides functionality for downloading one or more playlists.
"""

import time
import logging
from pathlib import Path
from typing import List, Dict, Optional

from ..core.settings import load_settings
from ..utils.console.manager import get_console
from ..core.downloader import SongDownloader, ThemeHelper
from ..playlist.cache.search_db import SearchFromPlaylistDataBase

logger = logging.getLogger(__name__)

console = get_console()

SETTINGS = load_settings()
playlist_dir_path = Path(SETTINGS.playlist_path).expanduser()


class DownloadPlaylist:
    """
    Class for downloading playlists.
    """

    def __init__(self, playlist_names: List[str]) -> None:
        """Initialize the DownloadPlaylist class."""
        self.playlists = playlist_names
        self.db_initializer.initialize_cache()
        self.db_searcher = SearchFromPlaylistDataBase()

    def download(
        self, format: Optional[str] = None, bitrate: Optional[str] = None
    ) -> bool:
        """
        Download all songs from the specified playlists.

        Args:
            format: Optional format for downloaded songs (mp3, flac, etc.)
            bitrate: Optional bitrate for downloaded songs (128k, 320k, etc.)

        Returns:
            bool: True if download was successful, False otherwise
        """
        _, active_theme_styles = ThemeHelper.retrieve_theme_gradients_and_styles()

        success_color = ThemeHelper.get_theme_color(
            active_theme_styles, "success", "green"
        )
        error_color = ThemeHelper.get_theme_color(active_theme_styles, "error", "red")
        accent_color = ThemeHelper.get_theme_color(
            active_theme_styles, "accent", "cyan"
        )

        if not self.playlists:
            console.print(
                f"[bold {error_color}]Error:[/] No playlists specified for download"
            )
            return False

        console.print(
            f"[bold {accent_color}]Downloading playlist:[/] {', '.join(self.playlists)}"
        )

        for playlist_name in self.playlists:
            try:
                songs_data = self._fetch_playlist_songs(playlist_name)

                if not songs_data:
                    console.print(
                        f"[bold {error_color}]Error:[/] No songs found in playlist '{playlist_name}'"
                    )
                    continue

                song_names = [song["track_name"] for song in songs_data]

                playlist_path = playlist_dir_path / playlist_name

                self._download_songs(song_names, playlist_path, format, bitrate)

                self._save_playlist_to_database(playlist_name, songs_data)

                console.print(
                    f"[bold {success_color}]Success:[/] Playlist '{playlist_name}' downloaded and saved"
                )

            except Exception as e:
                logger.error(
                    f"Error downloading playlist '{playlist_name}': {e}", exc_info=True
                )
                console.print(
                    f"[bold {error_color}]Error:[/] Failed to download playlist '{playlist_name}': {str(e)}"
                )
                return False

        return True

    def _fetch_playlist_songs(self, playlist_name: str) -> List[Dict[str, str]]:
        """
        Fetch the list of songs from a playlist using the SearchFromPlaylistDataBase.

        Args:
            playlist_name: Name of the playlist to fetch

        Returns:
            List of song dictionaries with metadata
        """
        try:
            playlist_data = (
                self.db_searcher.initialize_playlist_songs_dict_with_metadata(
                    playlist_name
                )
            )

            if playlist_name in playlist_data and playlist_data[playlist_name]:
                logger.info(
                    f"Found {len(playlist_data[playlist_name])} songs in playlist '{playlist_name}'"
                )
                return playlist_data[playlist_name]

            logger.info(f"No songs found in playlist '{playlist_name}' in database")

            return []

        except Exception as e:
            logger.error(f"Error fetching playlist songs: {e}", exc_info=True)
            console.print(f"[red]Error fetching songs from playlist: {str(e)}[/red]")
            return []

    def _download_songs(
        self,
        songs: List[str],
        output_dir: Path,
        format: Optional[str],
        bitrate: Optional[str],
    ) -> None:
        """
        Download songs using the SongDownloader.

        Args:
            songs: List of song names
            format: Optional format for downloaded songs
            bitrate: Optional bitrate for downloaded songs
        """
        downloader = SongDownloader(
            song_list_to_download=songs,
            download_path=output_dir,
            format=format,
            bitrate=bitrate,
        )

        downloader.download_songs()

    def _save_playlist_to_database(
        self, playlist_name: str, songs_data: List[Dict[str, str]]
    ) -> None:
        """
        Save the playlist and its songs to the database using the existing database updater.

        Args:
            playlist_name: Name of the playlist
            songs_data: List of song dictionaries with metadata
        """
        current_time = int(time.time())

        try:
            # Create or update the playlist
            playlist_id = self.db_updater.save_playlist(
                playlist_name=playlist_name,
                description=f"Downloaded playlist: {playlist_name}",
                created_at=current_time,
                updated_at=current_time,
            )

            # Save each song to the playlist with its metadata
            for song_data in songs_data:
                self.db_updater.save_song_to_playlist(
                    playlist_id=playlist_id,
                    track_name=song_data.get("track_name", ""),
                    url=song_data.get("url", ""),
                    artist_name=song_data.get("artist_name", ""),
                    album_name=song_data.get("album_name", ""),
                    thumbnail_url=song_data.get("thumbnail_url", ""),
                    duration=song_data.get("duration", 0),
                )

            logger.info(
                f"Playlist '{playlist_name}' saved to database with {len(songs_data)} songs"
            )
        except Exception as e:
            logger.error(f"Database error while saving playlist: {e}", exc_info=True)
            raise Exception(f"Database error: {str(e)}")
