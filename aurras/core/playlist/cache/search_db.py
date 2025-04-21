"""
Search Database Module

This module provides a class for searching songs in the playlist database.
"""

from typing import Dict, List
from .loader import LoadPlaylistData
from ....utils.handle_fuzzy_search import FuzzySearcher


class SearchFromPlaylistDataBase:
    """
    Class for searching song data in the playlist database.
    """

    def __init__(self):
        """
        Initializes the SearchFromPlaylistDataBase class.
        """
        self.load_playlist_data = LoadPlaylistData()
        self.fuzzy_search = FuzzySearcher(threshold=0.49)

    def initialize_playlist_dict(self) -> Dict[str, List[str]]:
        """
        Initializes a dictionary of playlists from the playlist database.

        Returns:
            dict: Dictionary with playlist name as key and list of song names as value
        """
        playlist_metadata_from_db = self.load_playlist_data.load_playlists()
        playlist_dict = {
            playlist["name"]: [song["track_name"] for song in playlist["songs"]]
            for playlist in playlist_metadata_from_db
        }

        return playlist_dict

    def initialize_all_playlist_songs_dict(self) -> Dict[str, List[str]]:
        """
        Initializes a dictionary of songs from the playlist database.

        Returns:
            dict: Dictionary with playlist name as key and list of song names as value
        """
        playlist_metadata_from_db = self.load_playlist_data.load_playlists()
        playlist_songs_dict = {
            playlist["name"]: [song["track_name"] for song in playlist["songs"]]
            for playlist in playlist_metadata_from_db
        }

        return playlist_songs_dict

    def initialize_all_playlists_songs_with_metadata_dict(
        self,
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Initializes a dictionary of songs with metadata from the complete playlist database.

        Returns:
            dict: Dictionary with playlist name as key and list of songs with metadata as value
        """
        playlist_metadata_from_db = self.load_playlist_data.load_playlists()
        playlist_songs_dict = {
            playlist["name"]: [
                {
                    "track_name": song["track_name"],
                    "url": song["url"],
                    "artist_name": song["artist_name"],
                    "album_name": song["album_name"],
                    "thumbnail_url": song["thumbnail_url"],
                    "duration": song["duration"],
                }
                for song in playlist["songs"]
            ]
            for playlist in playlist_metadata_from_db
        }

        return playlist_songs_dict

    def initialize_playlist_songs_dict(
        self,
        playlist_name: str,
    ) -> Dict[str, List[str]]:
        """
        Initializes a dictionary of songs for a specific playlist.

        Args:
            playlist_name: Name of the playlist to filter
        Returns:
            dict: Dictionary with playlist name as key and list of song names as value
        """
        playlist_metadata_from_db = self.load_playlist_data.load_playlists()
        playlist_songs_dict = {
            playlist["name"]: [song["track_name"] for song in playlist["songs"]]
            for playlist in playlist_metadata_from_db
            if playlist["name"] == playlist_name
        }

        return playlist_songs_dict

    def initialize_playlist_songs_dict_with_metadata(
        self,
        playlist_name: str,
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Initializes a dictionary of songs with metadata for a specific playlist.

        Args:
            playlist_name: Name of the playlist to filter
        Returns:
            dict: Dictionary with playlist name as key and list of song metadata as value
        """
        playlist_metadata_from_db = self.load_playlist_data.load_playlists()
        playlist_songs_dict = {
            playlist["name"]: [
                {
                    "track_name": song["track_name"],
                    "url": song["url"],
                    "artist_name": song["artist_name"],
                    "album_name": song["album_name"],
                    "thumbnail_url": song["thumbnail_url"],
                    "duration": song["duration"],
                }
                for song in playlist["songs"]
            ]
            for playlist in playlist_metadata_from_db
            if playlist["name"] == playlist_name
        }

        return playlist_songs_dict

    def search_for_playlists_by_name_or_artist(
        self, query: str
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Search for songs by name or artist using fuzzy matching.

        Args:
            query: Search term to look for in song names or artist names

        Returns:
            dict: Dictionary with playlist name as key and list of song metadata as value
        """
        playlists_found: Dict[str, List[Dict[str, str]]] = {}

        playlist_songs_dict = self.initialize_all_playlists_songs_with_metadata_dict()

        song_names: List[str] = []
        artist_names: List[str] = []

        for playlist in playlist_songs_dict:
            tracks = playlist_songs_dict[playlist]
            for track in tracks:
                song_names.append(track["track_name"])
                artist_names.append(track["artist_name"])

            if not self.fuzzy_search.find_best_match(
                query, song_names
            ) or not self.fuzzy_search.find_best_match(query, artist_names):
                continue

            playlists_found.update(
                self.initialize_playlist_songs_dict_with_metadata(playlist)
            )

        return playlists_found
