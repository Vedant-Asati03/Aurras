"""
Database Connection Module

This module provides a generic database connection manager that can be used
across the application to manage SQLite database connections.
"""

import sqlite3
import threading
from pathlib import Path
from aurras.utils.logger import get_logger

logger = get_logger("aurras.db_connection", log_to_console=False)


class DatabaseConnectionManager:
    """
    Generic database connection manager for SQLite databases.

    This class implements a thread-safe singleton pattern with connection pooling
    to ensure proper database access across different threads.
    """

    # Dictionary to store database path to instance mappings
    _instances = {}
    # Class-level lock for thread safety during instance creation
    _instance_lock = threading.RLock()

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

        with cls._instance_lock:
            if path_str not in cls._instances:
                instance = super(DatabaseConnectionManager, cls).__new__(cls)
                instance.db_path = db_path
                instance._connection = None
                instance._connection_lock = threading.RLock()
                cls._instances[path_str] = instance

            return cls._instances[path_str]

    def get_connection(self) -> sqlite3.Connection:
        """
        Get or create a database connection in a thread-safe manner.

        Returns:
            sqlite3.Connection: SQLite database connection
        """
        with self._connection_lock:
            if self._connection is None:
                # Use check_same_thread=False but manage thread safety with our locks
                self._connection = sqlite3.connect(
                    self.db_path, check_same_thread=False
                )
                self._connection.row_factory = sqlite3.Row
                logger.debug(f"Created new database connection to {self.db_path}")
            return self._connection

    def close(self) -> None:
        """
        Close the database connection.
        """
        with self._connection_lock:
            if self._connection:
                self._connection.close()
                logger.debug(f"Closed database connection to {self.db_path}")
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
        with self._connection_lock:
            if self._connection and not exc_type:
                self._connection.commit()
