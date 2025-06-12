"""
Search Database Module

This module provides a class for searching songs in the playlist database.
"""

from typing import Any, Dict, List, Optional
from aurras.utils.handle_fuzzy_search import FuzzySearcher
from aurras.core.playlist.cache.loader import LoadPlaylistData


class SearchFromPlaylistDataBase:
    """
    Class for searching song data in the playlist database.
    """

    def __init__(self):
        """
        Initializes the SearchFromPlaylistDataBase class.
        """
        self.load_playlist = LoadPlaylistData()
        self.fuzzy_search = FuzzySearcher(threshold=0.73)

    def create_song_artist_dict(
        self,
        playlist_name: Optional[str],
    ) -> Dict[str, List[str]]:
        """
        Initializes a dictionary of songs for a specific playlist.

        Args:
            playlist_name: Name of the playlist to filter

        Returns:
            dict: Dictionary with playlist name as key and list of song names as value
        """
        metadata = self.load_playlist.retireve_playlist_info_with_content(playlist_name)

        track_artist_dictionary = {
            song["track_name"]: song["artist_name"] for song in metadata
        }

        return track_artist_dictionary

    def create_playlist_tracks_dict(
        self,
        playlist_name: str = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Initializes a dictionary of songs with metadata from the complete playlist database.

        Returns:
            dict: Dictionary with playlist name as key and list of songs with metadata as value
        """
        if playlist_name:
            metadata = self.load_playlist.retireve_playlist_info_with_content(
                playlist_name
            )
            playlist_info = self.load_playlist.retrieve_playlist_info(playlist_name)

        else:
            metadata = self.load_playlist.retireve_playlist_info_with_content()
            playlist_info = self.load_playlist.retrieve_playlist_info()

        playlist_tracks_info = {
            playlist["name"]: [
                {
                    "track_name": song["track_name"],
                    "artist_name": song["artist_name"],
                }
                for song in metadata
                if song["playlist_id"] == playlist["id"]
            ]
            for playlist in playlist_info
        }

        return playlist_tracks_info

    def search_for_playlists_by_name_or_artist(self, query: str) -> List[str]:
        """
        Search for songs by name or artist using fuzzy matching.

        Args:
            query: Search term to look for in song names or artist names

        Returns:
            list: List of playlists containing the specified song or artist
        """
        playlists_found: List[str] = []

        playlist_songs_dict = self.create_playlist_tracks_dict()

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
        metadata = self.load_playlist.retrieve_playlist_info(playlist_name)
        playlist_info = metadata[0] if metadata else {}

        is_downloaded = playlist_info.get("is_downloaded", False)

        return is_downloaded

    def check_if_playlist_exists(self, playlist_name: str) -> bool:
        """
        Check if a playlist exists in the database.

        Args:
            playlist_name: Name of the playlist to check

        Returns:
            bool: True if the playlist exists, False otherwise
        """
        metadata = self.load_playlist.retrieve_playlist_info(playlist_name)
        return bool(metadata)
