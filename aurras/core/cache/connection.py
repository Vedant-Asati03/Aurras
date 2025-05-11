"""
Cache Database Connection Module

This module provides a singleton connection manager for the cache database.
"""

import sqlite3

from aurras.utils.path_manager import _path_manager


class CacheDatabaseConnection:
    """Singleton database connection manager for the cache database."""

    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheDatabaseConnection, cls).__new__(cls)
            cls._instance.db_path = _path_manager.cache_db
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        """Get or create a database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    @property
    def connection(self) -> sqlite3.Connection:
        """Property to directly access the connection."""
        return self.get_connection()

    def __enter__(self) -> sqlite3.Connection:
        """Context manager entry point."""
        return self.get_connection()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit point.

        Note: We don't close the connection here since it's a singleton that may
        be used elsewhere. Call close() explicitly when shutting down the application.
        """
        # We intentionally don't close the connection here to keep the singleton alive
        # Just commit any pending transactions
        if self._connection and not exc_type:
            self._connection.commit()
