"""
Song Downloader Module

This module provides a class for downloading songs without videos using SpotDL and moving them to a specified directory.

Example:
    ```python
    downloader = SongDownloader(song_list_to_download=["song_name_1", "song_name_2"], directory_to_save_in="your_directory_path")
    downloader.download_song()
    ```
"""

import sys
import asyncio
import subprocess
from pathlib import Path

# Fix import to use relative path instead of absolute
from ..utils.path_manager import PathManager

# Create a PathManager instance
_path_manager = PathManager()


class SongDownloader:
    """
    SongDownloader class for downloading songs without videos using SpotDL and moving them to a specified directory.

    Attributes:
        config (Config): An instance of the Config class.
        current_directory (Path): The current working directory.
        song_list_to_download (list): List of song names to download.
        directory_to_save_in (Path): The directory to save the downloaded songs in.

    Methods:
        __init__(self, song_list_to_download: list, directory_to_save_in: Path): Initializes the SongDownloader class.
        download_song(self): Download songs without videos and move them to the specified directory.
    """

    def __init__(self, song_list_to_download: list):
        """
        Initializes the SongDownloader class.

        Args:
            song_list_to_download (list): List of song names to download.
            directory_to_save_in (Path): The directory to save the downloaded songs in.
        """
        self.current_directory = Path.cwd()
        self.song_list_to_download = song_list_to_download

        # Use the path manager instance instead of importing from config
        _path_manager.downloaded_songs_dir.mkdir(parents=True, exist_ok=True)

    async def _import_spotdl(self):
        from spotdl import __main__ as spotdl

        return spotdl

    def download_song(self):
        """
        Download a song without videos using spotdl.

        This method downloads a song without videos using spotdl.
        """
        spotdl = asyncio.run(self._import_spotdl())

        print("Downloading songs...")
        # Use downloaded_songs_dir from the path manager
        subprocess.check_call(
            f"{sys.executable} {spotdl.__file__} {' '.join([f'"{song}"' for song in self.song_list_to_download])} -o {_path_manager.downloaded_songs_dir}",
            shell=True,
        )
        (_ := self.directory_to_save_in / ".spotdl-cache").unlink()
        from ..utils.terminal import clear_screen

        clear_screen()
