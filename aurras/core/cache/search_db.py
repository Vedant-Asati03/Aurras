"""
Search Database Module

This module provides a class for searching songs in the database.
"""

from typing import Dict, List, Tuple
from aurras.core.cache.loader import LoadSongHistoryData


class SearchFromSongDataBase:
    """
    Class for searching song data in the database.
    """

    def __init__(self):
        """
        Initializes the SearchSong class with the user-provided song name.
        """
        self.load_song_metadata = LoadSongHistoryData()

    def initialize_song_dict(self) -> Dict[str, Tuple[str, str]]:
        """
        Initializes a dictionary of songs from the database.
        For backwards compatibility, returns only query, name, and URL.

        Returns:
            dict: Dictionary with search query as key and (name, url) as value
        """
        song_metadata_from_db = self.load_song_metadata.load_song_metadata_from_db()
        song_dict: Dict[str, Tuple[str, str]] = {
            song_user_searched: (track_name, url)
            for song_user_searched, track_name, url in song_metadata_from_db
        }

        return song_dict

    def initialize_full_song_dict(self) -> Dict[str, Dict[str, str]]:
        """
        Initializes a complete dictionary of songs with all metadata.

        Returns:
            dict: Dictionary with search query as key and complete metadata as value
        """
        song_metadata_from_db = (
            self.load_song_metadata.load_song_full_metadata_from_db()
        )
        song_dict: Dict[str, Dict[str, str]] = {}

        for result in song_metadata_from_db:
            search_query: str = result[0]
            song_info = {
                "track_name": result[1],
                "url": result[2],
                "artist_name": result[3],
                "album_name": result[4],
                "thumbnail_url": result[5],
                "duration": result[6],
            }
            song_dict[search_query] = song_info

        return song_dict

    def search_by_name_or_artist(self, query: str) -> List[Dict]:
        """
        Search for songs by name or artist.

        Args:
            query: Search term to look for in song names or artist names

        Returns:
            List of matching song dictionaries
        """
        songs = self.load_song_metadata.load_song_with_lyrics(
            song_name=query, artist=query
        )
        return songs
