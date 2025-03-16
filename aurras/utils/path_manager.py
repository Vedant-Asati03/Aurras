"""
Path Manager Module

This module provides a centralized way to manage file paths in the Aurras application.
"""

import os
from pathlib import Path
import platform


class PathManager:
    """
    Manages paths for the application.

    This class provides access to all the important directories and files
    used by the application, ensuring they exist and are accessible.
    """

    def __init__(self):
        """Initialize path locations."""
        # Determine the base app directory based on the OS
        if platform.system() == "Windows":
            self.app_dir = Path(os.path.expandvars("%APPDATA%")) / "Aurras"
        else:
            self.app_dir = Path.home() / ".aurras"

        # Create the app directory if it doesn't exist
        self.app_dir.mkdir(parents=True, exist_ok=True)

        # Define instance attributes for critical directories
        self._config_dir = self.app_dir / "config"
        self._database_dir = self.app_dir / "database"
        self._downloaded_songs_dir = self.app_dir / "songs"
        self._playlists_dir = self.app_dir / "playlists"
        self._log_dir = self.app_dir / "logs"
        self._mpv_dir = self.app_dir / "mpv"

        # Create directories
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._database_dir.mkdir(parents=True, exist_ok=True)
        self._downloaded_songs_dir.mkdir(parents=True, exist_ok=True)
        self._playlists_dir.mkdir(parents=True, exist_ok=True)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._mpv_dir.mkdir(parents=True, exist_ok=True)

        # Define important file paths
        self.config_file = self._config_dir / "config.yaml"
        self.default_config = self._config_dir / "default_config.yaml"
        self.history_db = self._database_dir / "play_history.db"
        self.lyrics_cache_db = self._database_dir / "lyrics_cache.db"
        self.saved_playlists = self._database_dir / "saved_playlists.db"
        self.mpv_conf = self._mpv_dir / "mpv.conf"
        self.input_conf = self._mpv_dir / "input.conf"

    def construct_path(self, *path_parts):
        """
        Construct a file path within the Aurras directory.

        Args:
            *path_parts: Path parts to append to the base Aurras directory.

        Returns:
            Path: The constructed path.
        """
        return self.app_dir.joinpath(*path_parts)

    def list_directory(self, directory_path):
        """
        List contents of a directory, filtering out hidden files.

        Args:
            directory_path (Path): Path to the directory to list

        Returns:
            list: List of filenames in the directory
        """
        try:
            if not directory_path.exists():
                return []

            # Get all files/directories in the specified path
            items = os.listdir(directory_path)

            # Filter out hidden files (those starting with .)
            items = [item for item in items if not item.startswith(".")]

            # Sort alphabetically
            items.sort()

            return items

        except (FileNotFoundError, PermissionError):
            # Return empty list if directory doesn't exist or isn't accessible
            return []

    # Define properties for all directories with consistent naming
    @property
    def config_dir(self):
        """Path to the configuration directory."""
        return self._config_dir

    @property
    def database_dir(self):
        """Path to the database directory."""
        return self._database_dir

    @property
    def downloaded_songs_dir(self):
        """Path to the downloaded songs directory."""
        return self._downloaded_songs_dir

    @property
    def playlists_dir(self):
        """Path to the playlists directory."""
        return self._playlists_dir

    @property
    def log_dir(self):
        """Path to the log directory."""
        return self._log_dir

    @property
    def mpv_dir(self):
        """Path to the MPV directory."""
        return self._mpv_dir

    @property
    def log_file(self):
        """Path to the current log file."""
        return self._log_dir / f"{Path(__file__).stem}.log"

    @property
    def settings_file(self):
        """Path to the settings file."""
        return self._config_dir / "settings.yaml"

    @property
    def custom_settings_file(self):
        """Path to the custom settings file."""
        return self._config_dir / "custom_settings.yaml"

    @property
    def cache_db(self):
        """Path to the cache database."""
        return self._database_dir / "cache.db"

    @property
    def recommendation_db(self):
        """Path to the recommendation database."""
        return self._database_dir / "recommendation.db"

    @property
    def spotify_auth_db(self):
        """Path to the Spotify authentication cache."""
        return self._database_dir / "spotify_auth.db"
