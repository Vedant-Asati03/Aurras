"""
Cache Initialization Module

This module provides a class for initializing the search history database.
"""

class InitializeSearchHistoryDatabase:
    """
    Class for initializing the search history database.
    """

    def initialize_cache(self, connection=None):
        """
        Initializes the cache database with the required tables.

        Args:
            connection: An optional pre-existing database connection. If not provided,
                       a new connection will be created for initialization.
        """
        if connection:
            self._initialize_tables(connection)
        else:
            from aurras.utils.db_connection import DatabaseConnectionManager
            from aurras.utils.path_manager import _path_manager

            with DatabaseConnectionManager(_path_manager.cache_db) as db:
                self._initialize_tables(db)

    def _initialize_tables(self, connection):
        """
        Initialize the database tables using the provided connection.

        Args:
            connection: SQLite database connection
        """
        cursor = connection.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY,
                song_user_searched TEXT,
                track_name TEXT,
                url TEXT,
                artist_name TEXT,
                album_name TEXT,
                thumbnail_url TEXT,
                duration INTEGER DEFAULT 0,
                fetch_time INTEGER
            )"""
        )

        # Create indexes for faster searching
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_song_user_searched ON cache(song_user_searched)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_track_name ON cache(track_name)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_artist_name ON cache(artist_name)"
        )

        # Create lyrics table in the same database - preserving original field names
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lyrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_id INTEGER,
                synced_lyrics TEXT,
                plain_lyrics TEXT,
                fetch_time INTEGER,
                FOREIGN KEY (cache_id) REFERENCES cache(id)
            )
        """)

        # Create index for lyrics lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_id ON lyrics(cache_id)")
