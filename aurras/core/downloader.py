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
import logging
import sqlite3
import subprocess
import contextlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator, Tuple
from rich.console import Console

from ..utils.path_manager import PathManager
from ..utils.handle_fuzzy_search import FuzzySearcher

METADATA_FILE = "metadata.spotdl"
DEFAULT_BATCH_SIZE = 25
MAX_RETRIES = 3
RETRY_DELAY = 5

_path_manager = PathManager()
output_dir = str(_path_manager.downloaded_songs_dir)
console = Console()
logger = logging.getLogger(__name__)


@contextlib.contextmanager
def change_dir(new_dir: str) -> Iterator[None]:
    """Context manager for changing directory and returning to original."""
    old_dir = os.getcwd()
    try:
        os.chdir(new_dir)
        yield
    finally:
        os.chdir(old_dir)


class DatabaseConnection:
    """Singleton database connection manager."""

    _instance = None
    _connection = None

    def __new__(cls, db_path: Optional[Path] = None):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            if db_path:
                cls._instance.db_path = db_path
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        """Get or create a database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None


class DownloadsDatabase:
    """Manager for the downloaded songs database."""

    def __init__(self):
        """Initialize the downloads database."""
        self.db_path = _path_manager.downloads_db
        self.db_conn = DatabaseConnection(self.db_path)
        self._initialize_database()

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

            # Create lyrics table - Fixed the missing song_id foreign key
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS song_lyrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    song_id INTEGER NOT NULL,
                    fetch_time INTEGER,
                    FOREIGN KEY(song_id) REFERENCES downloaded_songs(id)
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

    def save_downloaded_song(self, song_data: Dict[str, Any]) -> int:
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

                # Insert song data with correct placeholders
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO downloaded_songs
                    (track_name, artist_name, album_name, duration, download_date, 
                     file_path, cover_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        song_data.get("name", ""),
                        song_data.get("artists", ""),
                        song_data.get("album_name", ""),
                        song_data.get("duration", 0),
                        int(time.time()),
                        song_data.get("file_path", ""),
                        song_data.get("cover_url", ""),
                    ),
                )

                # Get the ID of the inserted/updated record
                if cursor.lastrowid:
                    song_id = cursor.lastrowid
                else:
                    # If it was an update, get the ID by querying
                    cursor.execute(
                        """
                        SELECT id FROM downloaded_songs
                        WHERE track_name = ? AND artist_name = ? AND album_name = ?
                    """,
                        (
                            song_data.get("name", ""),
                            song_data.get("artists", ""),
                            song_data.get("album_name", ""),
                        ),
                    )
                    result = cursor.fetchone()
                    song_id = result[0] if result else 0

                # Save lyrics if available
                if song_data.get("synced_lyrics") or song_data.get("plain_lyrics"):
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO song_lyrics
                        (song_id, synced_lyrics, plain_lyrics, fetch_time)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            song_id,
                            song_data.get("synced_lyrics", ""),
                            song_data.get("plain_lyrics", ""),
                            int(time.time()),
                        ),
                    )

                conn.commit()
                logger.info(f"Saved song to database: {song_data.get('name', '')}")
                return song_id
        except sqlite3.Error as e:
            logger.error(f"Database error when saving song: {e}", exc_info=True)
            return 0

    def batch_save_songs(self, songs_data: List[Dict[str, Any]]) -> List[int]:
        """
        Save multiple songs to the database in a batch.

        Args:
            songs_data: List of dictionaries containing song metadata

        Returns:
            List of inserted/updated record IDs
        """
        ids = []
        for song_data in songs_data:
            song_id = self.save_downloaded_song(song_data)
            if song_id:
                ids.append(song_id)
        return ids

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
        format: str,
        database: Optional[DownloadsDatabase] = None,
    ):
        """
        Initialize the metadata extractor.

        Args:
            database: Optional database instance for dependency injection
        """
        self.database = database or DownloadsDatabase()
        self.output_dir = output_dir
        self._file_path_cache: Dict[Tuple[str, str], Optional[Path]] = {}

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
                        console.print(
                            "[yellow]No songs found in metadata file[/yellow]"
                        )
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
                    console.print(
                        "[red]Error: metadata.spotdl file contains invalid JSON[/red]"
                    )
                    logger.error("Invalid JSON in metadata.spotdl file")

        except FileNotFoundError:
            console.print(f"[red]Error: {METADATA_FILE} file not found[/red]")
            logger.error(f"{METADATA_FILE} file not found")
        except Exception as e:
            console.print(f"[red]Error extracting metadata: {str(e)}[/red]")
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
            console.print(
                "[red]No metadata found for the song. [orange]Database not updated![/orange][/red]"
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
            console.print(
                "[red]No metadata found for the song. [orange]Database not updated![/orange][/red]"
            )
            return {}

        data.update({"file_path": file_path})
        return data

    def _update_database(self, data: Dict[str, Any]) -> None:
        """Calls save_download_song method to update the database with metadata.

        Args:
            data: metadata to update
        """
        if data:
            self.database.save_downloaded_song(data)
        else:
            console.print(
                "[red]No metadata found for the song. [orange]Database not updated![/orange][/red]"
            )

    def _update_database_batch(self, data_batch: List[Dict[str, Any]]) -> None:
        """Updates database with a batch of metadata records.

        Args:
            data_batch: List of metadata records to update
        """
        if data_batch:
            song_ids = self.database.batch_save_songs(data_batch)
            logger.info(f"Batch processed {len(song_ids)} songs")
        else:
            console.print("[yellow]No metadata to update in batch[/yellow]")

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

        if file_path.exists():
            self._file_path_cache[cache_key] = file_path

        return file_path if file_path and file_path.exists() else None


class SongDownloader:
    """Class for downloading songs using spotdl's CLI but extracting metadata using the library."""

    def __init__(
        self,
        song_list_to_download: List[str],
        download_path=output_dir,
        format="mp3",
        bitrate="auto",
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
        self.download_path = download_path or str(
            self._path_manager.downloaded_songs_dir
        )
        self.format = format
        self.bitrate = bitrate
        self.metadata_extractor = ExtractMetadata(Path(self.download_path), self.format)

    def download_songs(self):
        """
        Download songs using subprocess for the actual download, but use SpotDL library for metadata.
        """
        if not self.song_list_to_download:
            console.print("[yellow]No songs provided for download[/yellow]")
            return

        try:
            console.print(f"Songs will be saved to: [cyan]{self.download_path}[/cyan]")
            if self._download_with_subprocess():
                # This way if download fails, we dont extract metadata
                with change_dir(self.download_path):
                    self.metadata_extractor.extract_metadata_from_spotdl_saved()

        except KeyboardInterrupt:
            console.print("[red]Downloading Cancelled![/red]")
            return
        except subprocess.CalledProcessError as e:
            logger.error(f"Subprocess error: {e}", exc_info=True)
            console.print(f"[bold red]Error running spotdl: {str(e)}[/bold red]")
        except Exception as e:
            logger.error(f"Failed to download songs: {e}", exc_info=True)
            console.print(f"[bold red]Error during download: {str(e)}[/bold red]")

    def _download_with_subprocess(self):
        """
        Download songs using spotdl via subprocess with retry mechanism.
        Uses a consistent output format to make filenames predictable.
        """
        # Format: {artist} - {title}.{output-ext}
        output_format = "{artists} - {title}"

        cmd_parts = [
            f"spotdl download {' '.join(f'"{item}"' for item in self.song_list_to_download)}",
            f'--output "{output_format}"',
        ]

        if self.format is not None:
            cmd_parts.append(f'--format "{self.format}"')

        if self.bitrate is not None:
            cmd_parts.append(f'--bitrate "{self.bitrate}"')

        cmd_parts.append("--ytm-data --preload --save-file metadata.spotdl")

        cmd = " ".join(cmd_parts)

        attempts = 0
        while attempts < MAX_RETRIES:
            try:
                with change_dir(self.download_path):
                    logger.info(
                        f"Downloading songs (attempt {attempts + 1}/{MAX_RETRIES})"
                    )
                    logger.debug(f"Running command: {cmd}")
                    subprocess.run(
                        cmd,
                        check=True,
                        shell=True,
                    )
                return True  # Success, exit the retry loop
            except subprocess.CalledProcessError as e:
                attempts += 1
                logger.warning(f"Download attempt {attempts} failed: {e}")
                if attempts < MAX_RETRIES:
                    console.print(
                        f"[yellow]Retrying download in {RETRY_DELAY} seconds...[/yellow]"
                    )
                    time.sleep(RETRY_DELAY)
                else:
                    console.print(
                        "[red]Max retry attempts reached. Download failed.[/red]"
                    )
                    raise
        return False  # In case we somehow exit the loop without returning
