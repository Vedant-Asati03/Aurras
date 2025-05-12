"""
Database Connection Module

This module provides a generic database connection manager that can be used
across the application to manage SQLite database connections.
"""

import sqlite3
from pathlib import Path


class DatabaseConnectionManager:
    """
    Generic database connection manager for SQLite databases.

    This class implements the singleton pattern to ensure only one connection
    is active for a specific database path. It can be used for any SQLite database
    across the application.
    """

    # Dictionary to store database path to instance mappings
    _instances = {}

    def __new__(cls, db_path: Path):
        """
        Create or retrieve a singleton instance for the given database path.

        Args:
            db_path (Path): Path to the SQLite database

        Returns:
            DatabaseConnectionManager: Singleton instance for the database path
        """
        # Convert Path to string for dictionary key
        path_str = str(db_path)

        if path_str not in cls._instances:
            instance = super(DatabaseConnectionManager, cls).__new__(cls)
            instance.db_path = db_path
            instance._connection = None
            cls._instances[path_str] = instance

        return cls._instances[path_str]

    def get_connection(self) -> sqlite3.Connection:
        """
        Get or create a database connection.

        Returns:
            sqlite3.Connection: SQLite database connection
        """
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def close(self) -> None:
        """
        Close the database connection.
        """
        if self._connection:
            self._connection.close()
            self._connection = None

    @property
    def connection(self) -> sqlite3.Connection:
        """
        Property to directly access the connection.

        Returns:
            sqlite3.Connection: SQLite database connection
        """
        return self.get_connection()

    def __enter__(self) -> sqlite3.Connection:
        """
        Context manager entry point.

        Returns:
            sqlite3.Connection: SQLite database connection
        """
        return self.get_connection()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit point.

        Note: We don't close the connection here since it's a singleton that may
        be used elsewhere. Call close() explicitly when shutting down the application.
        """
        # We intentionally don't close the connection here to keep the singleton alive
        # Just commit any pending transactions if no exception occurred
        if self._connection and not exc_type:
            self._connection.commit()
