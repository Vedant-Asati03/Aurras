"""
Song downloader module

This module provides a class for downloading songs using spotdl's CLI through subprocess
while extracting rich metadata using the library to store in the database.

Example:
    ```python
    downloader = SongDownloader(song_list_to_download=["song_name_1", "song_name_2"])
    downloader.download_songs()
    ```
"""

import os
import json
import time
import sqlite3
import subprocess
import contextlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator, Tuple

from aurras.utils.console import console
from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.utils.path_manager import _path_manager
from aurras.utils.handle_fuzzy_search import FuzzySearcher
from aurras.utils.db_connection import DatabaseConnectionManager

METADATA_FILE = "metadata.spotdl"
DEFAULT_BATCH_SIZE = 25
MAX_RETRIES = int(SETTINGS.maximum_retries)

logger = get_logger("aurras.core.downloader", log_to_console=False)


@contextlib.contextmanager
def change_dir(new_dir: str) -> Iterator[None]:
    """Context manager for changing directory and returning to original."""
    old_dir = os.getcwd()
    try:
        os.chdir(new_dir)
        yield
    finally:
        os.chdir(old_dir)


class DownloadsDatabase:
    """Manager for the downloaded songs database."""

    def __init__(self):
        """Initialize the downloads database."""
        self.db_conn = DatabaseConnectionManager(_path_manager.downloads_db)
        self._initialize_database()
        self.playlist_db = None  # Lazy initialization

    def _initialize_database(self):
        """Create the downloads database with proper schema and indexes."""
        with self.db_conn.get_connection() as conn:
            cursor = conn.cursor()

            # Create downloads table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS downloaded_songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_name TEXT NOT NULL,
                    artist_name TEXT,
                    album_name TEXT,
                    duration INTEGER,
                    download_date INTEGER,
                    file_path TEXT,
                    cover_url TEXT,
                    UNIQUE(track_name, artist_name, album_name)
                )
            """)

            # Create indexes for faster searching
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_track_name ON downloaded_songs(track_name)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_artist_name ON downloaded_songs(artist_name)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_album_name ON downloaded_songs(album_name)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_download_date ON downloaded_songs(download_date)"
            )

            conn.commit()

    def _get_playlist_db(self):
        """Lazy initialization of the playlist database connection."""
        if self.playlist_db is None:
            from .playlist.cache.updater import UpdatePlaylistDatabase

            self.playlist_db = UpdatePlaylistDatabase()
        return self.playlist_db

    def save_downloaded_song(self, batch_data: List[tuple]) -> int:
        """
        Save a downloaded song to the database.

        Args:
            song_data: Dictionary containing song metadata

        Returns:
            The ID of the inserted/updated record
        """
        try:
            with self.db_conn.get_connection() as conn:
                cursor = conn.cursor()

                cursor.executemany(
                    """
                    INSERT OR REPLACE INTO downloaded_songs
                    (track_name, artist_name, album_name, duration, download_date, 
                     file_path, cover_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    batch_data,
                )

                conn.commit()

        except sqlite3.Error as e:
            logger.error(f"Database error when saving song: {e}", exc_info=True)
            return 0

    def _flush_data_in_batch(self, songs_data: List[Dict[str, Any]]) -> List[tuple]:
        """
        Convert a list of dictionaries to a list of tuples for batch insertion.

        Args:
            songs_data: List of dictionaries containing song metadata

        Returns:
            List of tuples for batch insertion
        """
        download_time = int(time.time())

        songs_metadata_batch = [
            (
                data.get("name", ""),
                data.get("artists", ""),
                data.get("album_name", ""),
                data.get("duration", 0),
                download_time,
                data.get("file_path", ""),
                data.get("cover_url", ""),
            )
            for data in songs_data
        ]
        return songs_metadata_batch

    def batch_save_songs(
        self, songs_data: List[Dict[str, Any]], playlist: Optional[str]
    ):
        """
        Save multiple songs to the database in a batch.

        Args:
            songs_data: List of dictionaries containing song metadata
            playlist: Optional playlist name to add the songs to
        """
        if not songs_data:
            raise ValueError("No song data provided for batch saving")

        songs_metadata_batch = self._flush_data_in_batch(songs_data)

        self.save_downloaded_song(songs_metadata_batch)

        if playlist and songs_data:
            playlist_db = self._get_playlist_db()

            # Convert downloads format to playlist format
            download_time = int(time.time())
            playlist_songs_metadata = [
                (
                    data.get("name", ""),  # track_name
                    data.get("artists", ""),  # artist_name
                    "",  # placeholder for field 2
                    "",  # placeholder for field 3
                    download_time,  # added_at
                )
                for data in songs_data
            ]

            playlist_db.batch_save_songs_to_playlist(playlist, playlist_songs_metadata)

    def get_downloaded_songs(
        self,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "download_date",
        descending: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get a list of downloaded songs formatted as a dictionary with song names as keys.

        Args:
            limit: Maximum number of songs to return
            offset: Number of songs to skip (for pagination)
            order_by: Column to order results by
            descending: Whether to sort in descending order
            filters: Dictionary of column:value pairs to filter results

        Returns:
            Dictionary where keys are song names and values are song metadata dictionaries
        """
        try:
            with self.db_conn.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT id, track_name, artist_name, album_name, duration, 
                           download_date, file_path, cover_url 
                    FROM downloaded_songs
                """

                params = []

                # Add WHERE clauses for any filters
                if filters:
                    where_clauses = []
                    for column, value in filters.items():
                        if column in ["track_name", "artist_name", "album_name"]:
                            where_clauses.append(f"{column} LIKE ?")
                            params.append(f"%{value}%")
                        else:
                            where_clauses.append(f"{column} = ?")
                            params.append(value)

                    if where_clauses:
                        query += " WHERE " + " AND ".join(where_clauses)

                # Add ORDER BY clause
                direction = "DESC" if descending else "ASC"
                query += f" ORDER BY {order_by} {direction}"

                # Add LIMIT and OFFSET
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor.execute(query, params)

                # Convert the results to the requested format
                result = {}
                for row in cursor.fetchall():
                    song_dict = dict(row)
                    track_name: str = song_dict.get("track_name", "")

                    # Format the song data according to the requested format
                    song_data = {
                        "track_name": track_name,
                        "url": song_dict.get("file_path", ""),
                        "artist_name": song_dict.get("artist_name", ""),
                        "album_name": song_dict.get("album_name", ""),
                        "thumbnail_url": song_dict.get("cover_url", ""),
                        "duration": song_dict.get("duration", 0),
                    }

                    result[track_name] = song_data.copy()

                return result

        except sqlite3.Error as e:
            logger.error(f"Database error when fetching songs: {e}", exc_info=True)
            return {}


class ExtractMetadata:
    def __init__(
        self,
        output_dir: Path,
        database: Optional[DownloadsDatabase] = None,
        playlist: Optional[str] = None,
    ):
        """
        Initialize the metadata extractor.

        Args:
            database: Optional database instance for dependency injection
        """
        self.database = database or DownloadsDatabase()
        self.output_dir = output_dir
        self._file_path_cache: Dict[Tuple[str, str], Optional[Path]] = {}
        self.playlist = playlist

    def extract_metadata_from_spotdl_saved(self, batch_size: int = DEFAULT_BATCH_SIZE):
        """
        Extract metadata from the saved metadata.spotdl file and update the database.

        Args:
            batch_size: Number of songs to process in a batch
        """
        try:
            with open(METADATA_FILE, "r") as file:
                try:
                    songs_data = json.loads(file.read())

                    if not songs_data:
                        console.print_warning("No songs found in metadata file")
                        return

                    # Process songs in batches
                    songs_to_update = []
                    for song_data in songs_data:
                        song_name = song_data.get("name", "")
                        artists = song_data.get("artists", [])
                        artist_str = (
                            ", ".join(artists) if isinstance(artists, list) else artists
                        )

                        song_data = self._replace_artists_in_extracted_metadata(
                            data=song_data, artists=artist_str
                        )

                        file_path = self._find_downloaded_file(
                            artist_str, song_name, self.output_dir
                        )
                        if file_path:
                            song_data = self._add_filepath_to_extracted_metadata(
                                data=song_data, file_path=str(file_path)
                            )
                            if song_data:  # Skip empty metadata
                                songs_to_update.append(song_data)

                                # Process in batches
                                if len(songs_to_update) >= batch_size:
                                    self._update_database_batch(songs_to_update)
                                    songs_to_update = []

                    # Process any remaining songs
                    if songs_to_update:
                        self._update_database_batch(songs_to_update)

                except json.JSONDecodeError:
                    console.print_error(f"Invalid JSON in {METADATA_FILE} file")
                    logger.error("Invalid JSON in metadata.spotdl file")

        except FileNotFoundError:
            console.print_error(f"Error: {METADATA_FILE} file not found")
            logger.error(f"{METADATA_FILE} file not found")

        except Exception as e:
            console.print_error(f"Failed to extract metadata: {str(e)}")
            logger.error(f"Failed to extract metadata: {e}", exc_info=True)

    def _replace_artists_in_extracted_metadata(
        self, data: Dict[str, Any], artists: str
    ) -> Dict[str, Any]:
        """Replaces artists list with a string.

        Args:
            data: metadata to update
            artists: artists converted to string

        Returns:
            Updated metadata with replaced artists
        """
        if not data:
            console.print_error(
                "Error: No metadata found for the song. Database not updated!"
            )
            return {}

        data.update({"artists": artists})
        return data

    def _add_filepath_to_extracted_metadata(
        self, data: Dict[str, Any], file_path: str
    ) -> Dict[str, Any]:
        """Adds file path to the extracted metadata.

        Args:
            data: metadata to update
            file_path: path to the downloaded file

        Returns:
            Updated metadata with file path
        """
        if not data:
            console.print_error(
                "Error: No metadata found for the song. Database not updated!"
            )
            return {}

        data.update({"file_path": file_path})
        return data

    def _update_database_batch(self, data_batch: List[Dict[str, Any]]):
        """Updates database with a batch of metadata records.

        Args:
            data_batch: List of metadata records to update
        """
        if data_batch:
            # Update downloads database and playlist database
            self.database.batch_save_songs(data_batch, self.playlist)

            # Also update search cache database for consistency
            self._update_search_cache_database(data_batch)

        else:
            console.print_warning("No metadata to update in batch")

    def _find_downloaded_file(
        self, artist: str, title: str, output_dir: Path
    ) -> Optional[Path]:
        """
        Find the downloaded file based on artist and title.

        Args:
            artist: Artist name
            title: Song title
            output_dir: Directory where the file is downloaded

        Returns:
            Path to the downloaded file, or None if not found
        """
        # Check cache first
        cache_key = (artist.lower(), title.lower())
        if cache_key in self._file_path_cache:
            return self._file_path_cache[cache_key]

        all_files = os.listdir(output_dir)
        file_name = FuzzySearcher(threshold=0.5).find_best_match(
            f"{artist} - {title}", all_files
        )

        file_path = output_dir / file_name if file_name else None

        if file_path and file_path.exists():
            self._file_path_cache[cache_key] = file_path

        return file_path if file_path and file_path.exists() else None

    def _update_search_cache_database(self, data_batch: List[Dict[str, Any]]):
        """
        Update the search cache database with downloaded song metadata.
        This ensures songs downloaded via playlists are also searchable.

        Args:
            data_batch: List of metadata records to add to search cache
        """
        try:
            from aurras.core.cache.updater import UpdateSearchHistoryDatabase

            search_updater = UpdateSearchHistoryDatabase()

            for song_data in data_batch:
                # Extract relevant fields for search cache
                track_name = song_data.get("name", "")
                artist_name = song_data.get("artists", "")
                album_name = song_data.get("album_name", "")
                file_path = song_data.get("file_path", "")

                if track_name and file_path:
                    # Use track name as the search query (what user would search for)
                    search_updater.save_to_cache(
                        song_user_searched=track_name,
                        track_name=track_name,
                        url=file_path,  # Local file path as URL for downloaded songs
                        artist_name=artist_name,
                        album_name=album_name,
                        thumbnail_url="",  # No thumbnail for local files
                        duration=song_data.get("duration", 0),
                    )

            logger.info(f"Updated search cache database with {len(data_batch)} songs")

        except Exception as e:
            logger.warning(f"Failed to update search cache database: {str(e)}")
            # Don't raise the exception as this is a secondary operation


class SongDownloader:
    """Class for downloading songs using spotdl's CLI but extracting metadata using the library."""

    def __init__(
        self,
        song_list_to_download: List[str],
        playlist_path: str = None,
        download_path: str = None,
        format: str = None,
        bitrate: str = None,
    ):
        """
        Initialize the SongDownloader.

        Args:
            song_list_to_download: List of song names to download
            downlaod_path: Path to directory for song[s] to download in
            format: Format of the song[s] to download
            bitrate: Quality of the song[s] to download
            path_manager: Optional path manager for dependency injection
        """
        self._path_manager = _path_manager
        self.song_list_to_download = song_list_to_download
        self.download_path = self._setup_download_path(playlist_path, download_path)
        self.format = format if format is not None else SETTINGS.download_format
        self.bitrate = bitrate if bitrate is not None else SETTINGS.download_bitrate

        self.metadata_extractor = ExtractMetadata(
            output_dir=self.download_path, playlist=playlist_path
        )

    def _get_playlist_path(self, playlist_path: str = None) -> Optional[Path | None]:
        """
        Generate a download path if a playlist is provided.
        """
        if not playlist_path:
            return None

        playlist_dir = _path_manager.construct_path(
            _path_manager.playlists_dir, playlist_path
        )
        return playlist_dir

    def _setup_download_path(
        self, playlist_path: str = None, download_path: str = None
    ) -> Path:
        """
        Set up the download path for the songs.
        """
        if playlist_path := self._get_playlist_path(playlist_path):
            return Path(playlist_path).expanduser()

        # If no playlist, use the default download path
        return Path(
            download_path if download_path is not None else SETTINGS.download_path
        ).expanduser()

    def download_songs(self) -> bool:
        """
        Download songs using subprocess for the actual download, but use SpotDL library for metadata.

        Returns:
            bool: True if download was successful, False otherwise
        """
        if not self.song_list_to_download:
            console.print_warning("Warning: No songs provided for download")
            return False

        try:
            console.style_text(
                text=f"Songs will be saved to: {self.download_path}",
                style_key="accent",
                text_style="bold",
                print_it=True,
            )
            if self._download_with_subprocess():
                # This way if download fails, we dont extract metadata
                with change_dir(self.download_path):
                    self.metadata_extractor.extract_metadata_from_spotdl_saved()
                return True
            else:
                return False

        except KeyboardInterrupt:
            console.print_error("Download cancelled by user")
            return False

        except subprocess.CalledProcessError as e:
            logger.error(f"Subprocess error: {e}", exc_info=True)
            console.print_error(f"Error running spotdl: {str(e)}")
            return False

        except Exception as e:
            logger.error(f"Failed to download songs: {e}", exc_info=True)
            console.print_error(f"Error during download: {str(e)}")
            return False
            console.print_error(f"Error during download: {str(e)}")

    def _download_with_subprocess(self):
        """
        Download songs using spotdl via subprocess.
        Uses a consistent output format to make filenames predictable.
        Leverages spotdl's built-in retry mechanism.
        """
        # Format: {artist} - {title}.{output-ext}
        output_format = "{artists} - {title}"

        cmd_parts = [
            f"spotdl download {' '.join(f'"{item}"' for item in self.song_list_to_download)}",
            f'--output "{output_format}"',
        ]

        if self.format:
            cmd_parts.append(f'--format "{self.format}"')

        if self.bitrate:
            cmd_parts.append(f'--bitrate "{self.bitrate}"')

        cmd_parts.append(f"--max-retries {MAX_RETRIES}")

        cmd_parts.append("--ytm-data --preload --save-file metadata.spotdl")

        cmd = " ".join(cmd_parts)

        try:
            with change_dir(self.download_path):
                logger.info(
                    f"Downloading songs using spotdl with max retries: {MAX_RETRIES}"
                )
                logger.debug(f"Running command: {cmd}")

                console.style_text(
                    text=f"Download: {len(self.song_list_to_download)} songs",
                    style_key="accent",
                    text_style="bold",
                    print_it=True,
                )

                subprocess.run(
                    cmd,
                    check=True,
                    shell=True,
                )

            console.print_success(
                f"Complete: Successfully downloaded {len(self.song_list_to_download)} songs"
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Download failed: {e}")
            console.print_error(
                f"Error: Download failed after {MAX_RETRIES} retries. Please check your internet connection or the song names."
            )
            raise
