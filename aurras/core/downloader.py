"""
Song Downloader Module

This module provides a class for downloading songs without videos using SpotDL and moving them to a specified directory.

Example:
    ```python
    downloader = SongDownloader(song_list_to_download=["song_name_1", "song_name_2"])
    downloader.download_song()
    ```
"""

import sys
import os
import subprocess
import glob
from pathlib import Path

# Fix import to use relative path instead of absolute
from ..utils.path_manager import PathManager

# Create a PathManager instance
_path_manager = PathManager()


class SongDownloader:
    """
    SongDownloader class for downloading songs without videos using SpotDL and moving them to a specified directory.

    Attributes:
        current_directory (Path): The current working directory.
        song_list_to_download (list): List of song names to download.
    """

    def __init__(self, song_list_to_download: list):
        """
        Initializes the SongDownloader class.

        Args:
            song_list_to_download (list): List of song names to download.
        """
        self.current_directory = Path.cwd()
        self.song_list_to_download = song_list_to_download

        # Use the path manager instance instead of importing from config
        _path_manager.downloaded_songs_dir.mkdir(parents=True, exist_ok=True)

    def download_song(self):
        """
        Download songs without videos using spotdl.

        This method downloads songs without videos using the spotdl command-line tool.
        """
        print("Downloading songs...")

        # Format output directory path as a string
        output_dir = str(_path_manager.downloaded_songs_dir)
        print(f"Songs will be saved to: {output_dir}")

        # Change to a temporary directory for download
        original_dir = os.getcwd()
        os.chdir(output_dir)

        try:
            for song in self.song_list_to_download:
                print(f"Downloading: {song}")

                try:
                    # Use a simpler command format that's known to work
                    cmd = f'spotdl download "{song}"'
                    print(f"Running: {cmd}")

                    # Execute the download command
                    subprocess.run(cmd, shell=True, check=True)

                    # Check what files were downloaded
                    recent_files = glob.glob(f"{output_dir}/*")
                    print(f"Files in download directory: {len(recent_files)}")
                    if recent_files:
                        for f in recent_files[-3:]:  # Show the last 3 files
                            print(f"  - {os.path.basename(f)}")

                except subprocess.CalledProcessError as e:
                    print(f"Error downloading {song}: {e}")
                    print("Make sure you have spotdl installed correctly.")

                    # Try to install spotdl if it's not installed or not working
                    try:
                        print("Attempting to install/update spotdl...")
                        subprocess.check_call(
                            [
                                sys.executable,
                                "-m",
                                "pip",
                                "install",
                                "--upgrade",
                                "spotdl",
                            ]
                        )

                        # Try again with the same command
                        print(f"Retrying download for: {song}")
                        subprocess.run(cmd, shell=True, check=True)
                    except Exception as install_error:
                        print(f"Failed to fix spotdl installation: {install_error}")
                        break

            # List all files in the directory after downloads
            all_files = os.listdir(output_dir)
            print(f"Total files in download directory: {len(all_files)}")

        finally:
            # Change back to original directory
            os.chdir(original_dir)

            # Remove the spotdl cache file if it exists
            cache_file = _path_manager.downloaded_songs_dir / ".spotdl-cache"
            if cache_file.exists():
                cache_file.unlink()

        from ..utils.terminal import clear_screen

        print("Download process completed.")
