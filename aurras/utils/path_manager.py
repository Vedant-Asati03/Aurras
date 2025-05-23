"""
Path Manager Module

This module provides a centralized way to manage file paths in the Aurras application.
"""

from pathlib import Path


class PathManager:
    """
    Manages paths for the application.

    This class provides access to all the important directories and files
    used by the application, ensuring they exist and are accessible.
    """

    def __init__(self):
        """Initialize path locations."""
        self.app_dir = Path.home() / ".aurras"
        self.app_dir.mkdir(parents=True, exist_ok=True)

        # Define instance attributes for critical directories
        self._config_dir = self.app_dir / "config"
        self._credentials_dir = self.app_dir / "credentials"
        self._database_dir = self.app_dir / "database"
        self._downloaded_songs_dir = self.app_dir / "songs"
        self._playlists_dir = self.app_dir / "playlists"
        self._log_dir = self.app_dir / "logs"
        self._backups_storage_dir = Path("backups")
        self._backup_metadata_dir = Path("metadata")
        self._backup_logs_dir = self._backup_metadata_dir / "logs"

        # Create directories
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._credentials_dir.mkdir(parents=True, exist_ok=True)
        self._database_dir.mkdir(parents=True, exist_ok=True)
        self._downloaded_songs_dir.mkdir(parents=True, exist_ok=True)
        self._playlists_dir.mkdir(parents=True, exist_ok=True)
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def construct_path(self, *path_parts):
        """
        Construct a file path within the Aurras directory.

        Args:
            *path_parts: Path parts to append to the base Aurras directory.

        Returns:
            Path: The constructed path.
        """
        generated_path = self.app_dir.joinpath(*path_parts)
        generated_path.mkdir(parents=True, exist_ok=True)
        return generated_path

    @property
    def backups_storage_dir(self):
        """Path to the backup storage directory where individual backups are stored."""
        return self._backups_storage_dir

    @property
    def backup_metadata_dir(self):
        """Path to the backup metadata directory."""
        return self._backup_metadata_dir

    @property
    def backup_logs_dir(self):
        """Path to the backup logs directory."""
        return self._backup_logs_dir

    @property
    def config_dir(self):
        """Path to the configuration directory."""
        return self._config_dir

    @property
    def credentials_dir(self):
        """Path to the credentials directory."""
        return self._credentials_dir

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
    def log_file(self):
        """Path to the current log file."""
        return self._log_dir / f"{Path(__file__).stem}.log"

    @property
    def settings_file(self):
        """Path to the settings file."""
        return self._config_dir / "settings.yaml"

    @property
    def credentials_file(self):
        """Path to the credentials file."""
        return self._credentials_dir / "credentials.json"

    @property
    def cache_db(self):
        """Path to the unified cache database."""
        return self._database_dir / "cache.db"

    @property
    def recommendation_db(self):
        """Path to the recommendation database, storing song recommendations."""
        return self._database_dir / "recommendation.db"

    @property
    def downloads_db(self):
        """Path to the downloaded songs database."""
        return self._database_dir / "downloads.db"

    @property
    def playlists_db(self):
        """Path to the saved playlists database."""
        return self._database_dir / "playlists.db"

    @property
    def history_db(self):
        """Path to the play history database."""
        return self._database_dir / "play_history.db"


_path_manager = PathManager()
