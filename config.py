"""
Configuration Class

This class provides methods for constructing file paths in the Aurras application.

Attributes:
    construct_path: A class method for constructing file paths.
    list_directory: A method for listing directories from the specified path.

Example:
    ```
    cache_path = Config.construct_path("cache.db")
    saved_playlists = Config.construct_path("playlists.db")
    downloaded_playlists_path = Config.construct_path("Playlists")
    spotify_auth = Config.construct_path("spotify_auth.db")
    recommendation = Config.construct_path("recommendation.db")
    downloaded_songs = Config.construct_path("songs")
    mpv = Config.construct_path("mpv")
    mpv_conf = Config.construct_path(mpv, "mpv.conf")
    input_conf = Config.construct_path(mpv, "input.conf")
    ```
"""

from pathlib import Path


class Config:
    @classmethod
    def construct_path(cls, *path_parts):
        """
        Construct File Path

        Args:
            *path_parts (str): The specific path parts to be appended to the base Aurras directory.

        Returns:
            Path: The full file path constructed based on the provided path parts.
        """
        return Path.home() / ".aurras" / Path(*path_parts)

    def list_directory(self, directory_path):
        """
        List directories in the specified path.

        Args:
            directory_path (Path): The path to the directory.

        Returns:
            List[str]: A list of directory names.
        """
        return [entry.name for entry in directory_path.iterdir() if entry.is_dir()]


# cache.db
cache = Config.construct_path("cache.db")
# playlists
saved_playlists = Config.construct_path("playlists.db")
downloaded_playlists = Config.construct_path("playlists")
# spotify_auth.db
spotify_auth = Config.construct_path("spotify_auth.db")
# recommendation.db
recommendation = Config.construct_path("recommendation.db")
# songs
downloaded_songs = Config.construct_path("songs")
# mpv
mpv = Config.construct_path("mpv")
mpv_conf = Config.construct_path(mpv, "mpv.conf")
input_conf = Config.construct_path(mpv, "input.conf")
