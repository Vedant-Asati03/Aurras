"""
Cache management module for Aurras.

This package handles caching of song data and search history.
"""

from aurras.utils.logger import get_logger
from aurras.utils.path_manager import _path_manager
from aurras.utils.db_connection import DatabaseConnectionManager
from aurras.core.cache.initialize import InitializeSearchHistoryDatabase

logger = get_logger("aurras.core.cache", log_to_console=False)

cache_db_connection = DatabaseConnectionManager(_path_manager.cache_db)
logger.debug(f"Cache database connection initialized: {cache_db_connection.connection}")

# Initialize the cache database when the module is imported
InitializeSearchHistoryDatabase().initialize_cache(cache_db_connection.connection)
logger.debug(f"Cache database initialized: {cache_db_connection.connection}")

__all__ = [
    "cache_db_connection",
]
