"""
Cache Update Module

This module provides a class for updating the search history database.
"""

import sqlite3

# Replace absolute import
from ...utils.path_manager import PathManager

_path_manager = PathManager()

from .initialize import InitializeSearchHistoryDatabase


class UpdateSearchHistoryDatabase:
    """
    Class for updating the search history database.
    """

    def __init__(self) -> None:
        """Initialize the cache if needed."""
        InitializeSearchHistoryDatabase().initialize_cache()

    def save_to_cache(self, song_user_searched, song_name_searched, song_url_searched):
        """
        Saves the searched song and its URL to the cache in the SQLite database.

        Args:
            song_user_searched (str): The song query entered by the user
            song_name_searched (str): The actual name of the song as found
            song_url_searched (str): The URL of the song
        """
        with sqlite3.connect(_path_manager.cache_db) as cache_db:
            cursor = cache_db.cursor()
            cursor.execute(
                "INSERT INTO cache (song_user_searched, song_name_searched, song_url_searched) VALUES (:song_user_searched, :song_name_searched, :song_url_searched)",
                {
                    "song_user_searched": song_user_searched,
                    "song_name_searched": song_name_searched,
                    "song_url_searched": song_url_searched,
                },
            )
