"""
Song Downloader Module

This module provides a class for downloading songs without videos using spotdl and moving them to a specified directory.

Example:
    ```python
    downloader = SongDownloader(song_list_to_download=["song_name_1", "song_name_2"], directory_to_save_in="your_directory_path")
    downloader.download_song()
    ```
"""

import sys
import subprocess
from pathlib import Path

from spotdl import __main__ as spotdl

import config as path
from term_utils import clear_screen


class SongDownloader:
    """
    Class for downloading songs without videos using spotdl and moving them to a specified directory.

    Attributes:
        song_list_to_download (list): List of song names to download.
        directory_to_save_in (Path): The directory to save the downloaded songs in.

    Methods:
        __init__(self, song_list_to_download: list, directory_to_save_in: Path): Initializes the SongDownloader class.
        _download_with_spotdl(self, song_to_download: str): Download a song without videos using spotdl.
        download_song(self): Download songs without videos and move them to the specified directory.
    """

    def __init__(self, song_list_to_download: list, directory_to_save_in: Path):
        """
        Initializes the SongDownloader class.

        Args:
            song_list_to_download (list): List of song names to download.
            directory_to_save_in (Path): The directory to save the downloaded songs in.
        """
        self.song_list_to_download = song_list_to_download
        self.directory_to_save_in = directory_to_save_in

        try:
            path.downloaded_songs.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            pass

    def _download_with_spotdl(self, song_to_download: str):
        """
        Download a song without videos using spotdl.

        Args:
            song_name (str): The name of the song to download.

        This method downloads a song without videos using spotdl.
        """
        subprocess.check_call([sys.executable, spotdl.__file__, song_to_download])

    def download_song(self):
        """
        Download songs without videos and move them to the specified directory.

        This method downloads songs using spotdl without videos and moves them to the designated directory.
        """
        for song_to_download in self.song_list_to_download:
            self._download_with_spotdl(song_to_download)
            clear_screen()

        for downloaded_song in path.downloaded_songs.iterdir():
            if downloaded_song.suffix == ".mp3":
                downloaded_song.rename(self.directory_to_save_in / downloaded_song.name)
