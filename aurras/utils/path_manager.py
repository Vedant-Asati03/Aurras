"""
Path Manager Module

This module provides a centralized way to manage file paths in the Aurras application.
"""

from pathlib import Path


class PathManager:
    """
    Class for managing file paths in the Aurras application.

    This class provides methods for constructing file paths and
    accessing common paths used throughout the application.
    """

    def __init__(self):
        """Initialize the PathManager class."""
        self._base_dir = Path.home() / ".aurras"
        self._base_dir.mkdir(parents=True, exist_ok=True)

        # Create required directories
        self.playlists_dir.mkdir(parents=True, exist_ok=True)
        self.downloaded_songs_dir.mkdir(parents=True, exist_ok=True)
        self.mpv_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def construct_path(self, *path_parts):
        """
        Construct a file path within the Aurras directory.

        Args:
            *path_parts: Path parts to append to the base Aurras directory.

        Returns:
            Path: The constructed path.
        """
        return self._base_dir.joinpath(*path_parts)

    def list_directory(self, directory_path):
        """
        List entries in the specified directory.

        Args:
            directory_path (Path): The directory to list.

        Returns:
            list: A list of directory entry names.
        """
        if not directory_path.exists():
            return []

        return [entry.name for entry in directory_path.iterdir()]

    @property
    def cache_db(self):
        """Path to the cache database."""
        return self.construct_path("cache.db")

    @property
    def saved_playlists(self):
        """Path to the saved playlists database."""
        return self.construct_path("playlists.db")

    @property
    def playlists_dir(self):
        """Path to the playlists directory."""
        return self.construct_path("playlists")

    @property
    def spotify_auth(self):
        """Path to the Spotify authentication database."""
        return self.construct_path("spotify_auth.db")

    @property
    def recommendation_db(self):
        """Path to the recommendation database."""
        return self.construct_path("recommendation.db")

    @property
    def downloaded_songs_dir(self):
        """Path to the downloaded songs directory."""
        return self.construct_path("songs")

    @property
    def mpv_dir(self):
        """Path to the MPV directory."""
        return self.construct_path("mpv")

    @property
    def mpv_conf(self):
        """Path to the MPV configuration file."""
        return self.mpv_dir / "mpv.conf"

    @property
    def input_conf(self):
        """Path to the input configuration file."""
        return self.mpv_dir / "input.conf"

    @property
    def logs_dir(self):
        """Path to the logs directory."""
        return self.construct_path("logs")

    @property
    def log_file(self):
        """Path to the current log file."""
        return self.logs_dir / f"{Path(__file__).stem}.log"

    @property
    def settings_file(self):
        """Path to the settings file."""
        return self.construct_path("settings.yaml")

    @property
    def custom_settings_file(self):
        """Path to the custom settings file."""
        return self.construct_path("custom_settings.yaml")
