"""
Configuration Class

This class provides methods for constructing file paths in the Aurras application.

Attributes:
    construct_path: A class method for constructing file paths.

Example:
    ```
    cache_path = Config.construct_path("cache.db")
    saved_playlists = Config.construct_path("playlists.db")
    downloaded_playlists_path = Config.construct_path("Playlists")
    spotify_auth = Config.construct_path("spotify_auth.db")
    recommendation = Config.construct_path("recommendation.db")
    downloaded_songs = Config.construct_path("songs")
    mpv = Config.construct_path("mpv")
    mpv_conf = Config.construct_path(os.path.join(mpv, "mpv.conf"))
    input_conf = Config.construct_path(os.path.join(mpv, "input.conf"))
    ```
"""

import os


class Config:
    @classmethod
    def construct_path(cls, path: str):
        """
        Construct File Path

        Args:
            path (str): The specific path to be appended to the base Aurras directory.

        Returns:
            str: The full file path constructed based on the provided path.
        """
        return os.path.join(os.path.expanduser("~"), ".aurras", path)


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
mpv_conf = Config.construct_path(os.path.join(mpv, "mpv.conf"))
input_conf = Config.construct_path(os.path.join(mpv, "input.conf"))
