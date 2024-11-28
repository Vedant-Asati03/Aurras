import sqlite3

from config import path
from libs.manage_cache.initialize_cache import InitializeSearchHistoryDataBase


class UpdateSearchHistoryDatabase:
    def __init__(self) -> None:
        InitializeSearchHistoryDataBase().initialize_cache()

    def save_to_cache(self, song_user_searched, song_name_searched, song_url_searched):
        """
        Saves the searched song and its URL to the cache in the SQLite database.
        """
        with sqlite3.connect(path.cache) as cache:
            cursor = cache.cursor()
            cursor.execute(
                "INSERT INTO cache (song_user_searched, song_name_searched, song_url_searched) VALUES (:song_user_searched, :song_name_searched, :song_url_searched)",
                {
                    "song_user_searched": song_user_searched,
                    "song_name_searched": song_name_searched,
                    "song_url_searched": song_url_searched,
                },
            )
