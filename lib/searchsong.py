"""
Module: search_song.py

This module provides a class for searching songs on YouTube and caching the results.

Classes:
- SearchSong: Class for searching songs on YouTube and caching the results.
  - Methods:
    - __init__(self, song_user_searched): Initializes the SearchSong class with the user-provided song name.
    - _initialize_cache(self): Initializes the cache by creating a SQLite database table if it doesn't exist and retrieves existing song-url pairs.
    - _search_on_youtube(self): Searches for the user-provided song on YouTube using yt_dlp and extracts information such as title and webpage URL.
    - _save_to_cache(self): Saves the searched song and its URL to the cache in the SQLite database.
    - search_song(self): Main method for searching a song. Checks the cache for similar songs and searches on YouTube if not found.

"""

import sqlite3
import yt_dlp

import config.config as path


class SearchSong:
    """
    Class for searching songs on YouTube and caching the results.

    Attributes:
        ydl_opts (dict): Options for the YouTube-DL library used for searching on YouTube.
        song_user_searched (str): The name of the song provided by the user.
        song_url_pairs (list): List of tuples containing pairs of song names and their corresponding YouTube URLs.
        song_name_searched (str): The name of the searched song.
        song_url_searched (str): The URL of the searched song on YouTube.

    Methods:
        __init__(self, song_user_searched): Initializes the SearchSong class with the user-provided song name.
        _initialize_cache(self): Initializes the cache by creating a SQLite database table if it doesn't exist and retrieves existing song-url pairs.
        _search_on_youtube(self): Searches for the user-provided song on YouTube using yt_dlp and extracts information such as title and webpage URL.
        _save_to_cache(self): Saves the searched song and its URL to the cache in the SQLite database.
        search_song(self): Main method for searching a song. Checks the cache for similar songs and searches on YouTube if not found.
    """

    def __init__(self, song_user_searched):
        """
        Initializes the SearchSong class with the user-provided song name.

        Args:
            song_user_searched (str): The name of the song provided by the user.
        """
        self.ydl_opts = {
            "quiet": "True",
            "noplaylist": "True",
            "format": "bestaudio",
            "skipdownload": "True",
            "youtube_skip_dash_manifest": "True",
            "sponsorblockremove": "song,sponsor,subscribe",
        }
        self.song_user_searched = song_user_searched
        self.song_url_pairs = None
        self.song_name_searched = None
        self.song_url_searched = None
        self._initialize_cache()

    def _initialize_cache(self):
        """
        Initializes the cache by creating a SQLite database table if it doesn't exist
        and retrieves existing song-url pairs.
        """
        with sqlite3.connect(path.cache) as cache:
            cursor = cache.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS cache (song_user_searched TEXT, song_name_searched TEXT, song_url_searched TEXT)"""
            )
            cursor.execute(
                "SELECT song_user_searched, song_name_searched, song_url_searched FROM cache"
            )
            self.song_url_pairs = cursor.fetchall()

    def _search_on_youtube(self):
        """
        Searches for the user-provided song on YouTube using yt_dlp
        and extracts information such as title and webpage URL.
        """
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                audio = ydl.extract_info(
                    f"ytsearch:{self.song_user_searched}", download=False
                )["entries"][0]
            except Exception:
                audio = ydl.extract_info(self.song_user_searched, download=False)

        self.song_name_searched = audio["title"]
        self.song_url_searched = audio["webpage_url"]

        self._save_to_cache()
        print("edited")

    def _save_to_cache(self):
        """
        Saves the searched song and its URL to the cache in the SQLite database.
        """
        with sqlite3.connect(path.cache) as cache:
            cursor = cache.cursor()
            cursor.execute(
                "INSERT INTO cache (song_user_searched, song_name_searched, song_url_searched) VALUES (:song_user_searched, :song_name_searched, :song_url_searched)",
                {
                    "song_user_searched": self.song_user_searched,
                    "song_name_searched": self.song_name_searched,
                    "song_url_searched": self.song_url_searched,
                },
            )

    def search_song(self):
        """
        Main method for searching a song. Checks the cache for similar songs
        and searches on YouTube if not found.
        """
        song_dict = {
            song_user_searched: (song_name_searched, song_url_searched)
            for song_user_searched, song_name_searched, song_url_searched in self.song_url_pairs
        }

        if self.song_user_searched in song_dict:
            self.song_name_searched, self.song_url_searched = song_dict[
                self.song_user_searched
            ]

        else:
            self._search_on_youtube()
