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
import subprocess
from pathlib import Path

from config import path
from lib.term_utils import clear_screen


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

    def __init__(self, song_list_to_download: list, directory_to_save_in: Path):
        """
        Initializes the SongDownloader class.

        Args:
            song_list_to_download (list): List of song names to download.
            directory_to_save_in (Path): The directory to save the downloaded songs in.
        """
        self.config = path.Config()
        self.current_directory = Path.cwd()
        self.song_list_to_download = song_list_to_download
        self.directory_to_save_in = directory_to_save_in

        path.downloaded_songs.mkdir(parents=True, exist_ok=True)

    def download_song(self):
        """
        Download a song without videos using spotdl.

        This method downloads a song without videos using spotdl.
        """
        from spotdl import __main__ as spotdl

        subprocess.check_call(
            f"{sys.executable} {spotdl.__file__} {' '.join([f'\"{song}\"' for song in self.song_list_to_download])} -o {self.directory_to_save_in}",
            shell=True,
        )
        (_ := self.directory_to_save_in / ".spotdl-cache").unlink()
        clear_screen()
