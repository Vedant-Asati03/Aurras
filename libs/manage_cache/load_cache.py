import sqlite3

from config import path
from libs.manage_cache.initialize_cache import InitializeSearchHistoryDataBase


class LoadSongHistoryData:
    def __init__(self) -> None:
        InitializeSearchHistoryDataBase().initialize_cache()

    def load_song_metadata_from_db(self):
        with sqlite3.connect(path.cache) as cache:
            cursor = cache.cursor()
            cursor.execute(
                "SELECT song_user_searched, song_name_searched, song_url_searched FROM cache"
            )
        song_metadata_from_db = cursor.fetchall()

        return song_metadata_from_db
