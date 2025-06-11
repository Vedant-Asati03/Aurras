"""
Playlist cache management module.

This package handles caching of playlist data and search history.

This module is responsible for managing the cache of playlists, including loading, saving, and clearing cached playlists. It also provides functionality for managing the cache of search history, including loading, saving, and
clearing cached search history.
"""

from aurras.utils.logger import get_logger
from aurras.utils.path_manager import _path_manager
from aurras.utils.db_connection import DatabaseConnectionManager
from aurras.core.playlist.cache.initialize import InitializePlaylistDatabase

logger = get_logger("aurras.core.playlist.cache", log_to_console=False)

playlist_db_connection = DatabaseConnectionManager(_path_manager.playlists_db)
logger.debug(
    f"Playlist cache database connection initialized: {_path_manager.playlists_db}"
)

# Initialize the playlist database when the module is imported
InitializePlaylistDatabase().initialize_cache(playlist_db_connection.connection)
logger.debug(f"Playlist cache database initialized: {_path_manager.playlists_db}")


__all__ = [
    "InitializePlaylistDatabase",
    "playlist_db_connection",
]
