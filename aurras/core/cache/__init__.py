"""
Cache management module for Aurras.

This package handles caching of song data and search history.
"""

from aurras.utils.db_connection import DatabaseConnectionManager
from aurras.core.cache.initialize import InitializeSearchHistoryDatabase
from aurras.utils.path_manager import _path_manager

cache_db_connection = DatabaseConnectionManager(_path_manager.cache_db)

# Initialize the cache database when the module is imported
InitializeSearchHistoryDatabase().initialize_cache(cache_db_connection.connection)

__all__ = [
    "cache_db_connection",
]
