"""
Search Database Module

This module provides a class for searching songs in the playlist database.
"""

from typing import Any, Dict, List, Optional
from aurras.core.playlist.cache.loader import LoadPlaylistData
from aurras.utils.handle_fuzzy_search import FuzzySearcher


class SearchFromPlaylistDataBase:
    """
    Class for searching song data in the playlist database.
    """

    def __init__(self):
        """
        Initializes the SearchFromPlaylistDataBase class.
        """
        self.load_playlist_data = LoadPlaylistData()
        self.fuzzy_search = FuzzySearcher(threshold=0.73)

    def _retrieve_correct_playlist_name(self, playlist_name: str) -> Optional[str]:
        """
        Retrieves the correct playlist name from the database using fuzzy matching.
        This is useful for correcting typos or variations in playlist names.

        Args:
            playlist_name: Name of the playlist to filter

        Returns:
            str: Corrected playlist name if found, None otherwise
        """
        playlists_metadata = self.initialize_playlist_metadata()

        playlists = [data["name"] for data in playlists_metadata]

        if corrected_playlist_name := self.fuzzy_search.find_best_match(
            playlist_name, playlists
        ):
            return corrected_playlist_name

    def initialize_playlist_metadata(
        self,
        playlist_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initializes a dictionary of songs for a specific playlist.

        Args:
            playlist_name: Name of the playlist to filter
        Returns:
            dict: Dictionary with playlist name as key and list of song names as value
        """
        playlists_metadata = self.load_playlist_data.load_playlists_with_partial_data()

        if not playlist_name:
            return playlists_metadata

        corrected_playlist_name = self._retrieve_correct_playlist_name(playlist_name)

        if not corrected_playlist_name:
            return {}

        if playlist_metadata := [
            data
            for data in playlists_metadata
            if data["name"] == corrected_playlist_name
        ]:
            return playlist_metadata[0]

    def initialize_all_playlist_songs_dict(
        self, playlist_name: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Initializes a dictionary of songs from the playlist database.

        Returns:
            dict: Dictionary with playlist name as key and list of song names as value
        """
        playlists_metadata = self.load_playlist_data.load_playlists_with_partial_data()

        playlist_songs_dict = {
            playlist["name"]: [song["track_name"] for song in playlist["songs"]]
            for playlist in playlists_metadata
        }

        return playlist_songs_dict

    def initialize_playlist_songs_dict(
        self,
        playlist_name: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        """
        Initializes a dictionary of songs for a specific playlist.

        Args:
            playlist_name: Name of the playlist to filter

        Returns:
            dict: Dictionary with playlist name as key and list of song names as value
        """
        playlist_metadata = (
            self.load_playlist_data.load_playlist_songs_with_full_metadata(
                playlist_name
            )
        )

        playlist_songs_dict = {
            song["track_name"]: [song["artist_name"], song["album_name"]]
            for song in playlist_metadata
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
        playlist_metadata_from_db = (
            self.load_playlist_data.load_playlists_with_complete_data()
        )
        # print(playlist_metadata_from_db)

        playlist_songs_dict = {
            playlist["name"]: [
                {
                    "track_name": song["track_name"],
                    "artist_name": song["artist_name"],
                    "album_name": song["album_name"],
                }
                for song in playlist["songs"]
            ]
            for playlist in playlist_metadata_from_db
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
        playlist_metadata_from_db = (
            self.load_playlist_data.load_playlists_with_partial_data()
        )
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

    def search_for_playlists_by_name_or_artist(self, query: str) -> List[str]:
        """
        Search for songs by name or artist using fuzzy matching.

        Args:
            query: Search term to look for in song names or artist names

        Returns:
            list: List of playlists containing the specified song or artist
        """
        playlists_found: List[str] = []

        playlist_songs_dict = self.initialize_all_playlists_songs_with_metadata_dict()

        song_names: List[str] = []
        artist_names: List[str] = []

        for playlist in playlist_songs_dict:
            tracks = playlist_songs_dict[playlist]
            for track in tracks:
                song_names.append(track["track_name"])
                artist_names.append(track["artist_name"])

            if self.fuzzy_search.find_best_match(
                query, song_names
            ) or self.fuzzy_search.find_best_match(query, artist_names):
                playlists_found.append(playlist)

        return playlists_found

    def check_if_playlist_is_downloaded(self, playlist_name: str) -> bool:
        """
        Check if a playlist is already downloaded.

        Args:
            playlist_name: Name of the playlist to check

        Returns:
            bool: True if the playlist is already downloaded, False otherwise
        """
        playlist_metadata = self.initialize_playlist_metadata(playlist_name)

        is_downloaded = playlist_metadata.get("is_downloaded", False)

        return is_downloaded
