"""
Playlist cache management module.

This package handles caching of playlist data and search history.

This module is responsible for managing the cache of playlists, including loading, saving, and clearing cached playlists. It also provides functionality for managing the cache of search history, including loading, saving, and
clearing cached search history.
"""

from aurras.utils.db_connection import DatabaseConnectionManager
from aurras.core.playlist.cache.initialize import InitializePlaylistDatabase
from aurras.utils.path_manager import _path_manager

playlist_db_connection = DatabaseConnectionManager(_path_manager.cache_db)

# Initialize the playlist database when the module is imported
InitializePlaylistDatabase().initialize_cache(playlist_db_connection.connection)

__all__ = [
    "InitializePlaylistDatabase",
    "playlist_db_connection",
]
