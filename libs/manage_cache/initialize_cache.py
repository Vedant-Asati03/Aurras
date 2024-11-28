import sqlite3
from config import path


class InitializeSearchHistoryDataBase:
    def __init__(self) -> None:
        self.song_url_pairs = None

    def initialize_cache(self):
        """
        Initializes the cache by creating a SQLite database table if it doesn't exist
        and retrieves existing song-url pairs.
        """
        with sqlite3.connect(path.cache) as cache:
            cursor = cache.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS cache (song_user_searched TEXT, song_name_searched TEXT, song_url_searched TEXT)"""
            )
