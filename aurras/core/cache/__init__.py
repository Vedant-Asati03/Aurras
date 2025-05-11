"""
Cache management module for Aurras.

This package handles caching of song data and search history.
"""

from aurras.core.cache.initialize import InitializeSearchHistoryDatabase
from aurras.core.cache.connection import CacheDatabaseConnection
from aurras.core.cache.loader import LoadSongHistoryData
from aurras.core.cache.updater import UpdateSearchHistoryDatabase

db_connection = CacheDatabaseConnection()
InitializeSearchHistoryDatabase().initialize_cache(db_connection.connection)

__all__ = [
    "CacheDatabaseConnection",
    "LoadSongHistoryData",
    "UpdateSearchHistoryDatabase",
    "InitializeSearchHistoryDatabase",
]
