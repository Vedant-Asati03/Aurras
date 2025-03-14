"""
YouTube Search Module

This module provides functionality for searching songs on YouTube.
"""

from math import e
from ...core.cache.updater import UpdateSearchHistoryDatabase
from ytmusicapi import YTMusic

from ...core.cache.search_db import SearchFromSongDataBase


class SongMetadata:
    """Class for storing song metadata."""

    def __init__(self):
        """Initialize the SongMetadata class."""
        self.song_name_searched = None
        self.song_url_searched = None
        self.song_thumbnail_url = None
        self.song_duration = None


class SearchSong(SongMetadata):
    def __init__(self, song_user_searched) -> None:
        self.update_song_history = UpdateSearchHistoryDatabase()
        self.search_from_yt = SearchFromYoutube(song_user_searched)
        self.search_from_db = SearchFromSongDataBase()
        self.song_user_searched = song_user_searched

    def search_song(self):
        """
        Main method for searching a song. Checks the cache for similar songs
        and searches on YouTube if not found.
        """
        song_dict = self.search_from_db.initialize_song_dict()

        if self.song_user_searched in song_dict:
            (
                self.song_name_searched,
                self.song_url_searched,
            ) = song_dict[self.song_user_searched]

        else:
            self.search_from_yt.search_from_youtube()

            self.song_name_searched = self.search_from_yt.song_name_searched
            self.song_url_searched = self.search_from_yt.song_url_searched

            self.update_song_history.save_to_cache(
                self.song_user_searched,
                self.search_from_yt.song_name_searched,
                self.search_from_yt.song_url_searched,
            )


class SearchFromYoutube(SongMetadata):
    def __init__(self, song_user_searched) -> None:
        super().__init__()
        self.song_user_searched = song_user_searched
        self.temporary_metadata_storage = dict()

    def _update_temporary_storage(self):
        """
        Updates the temporary storage with the song name and its URL.
        """
        self.temporary_metadata_storage.update(
            {self.song_name_searched: self.song_url_searched}
        )

    def _get_temporary_url(self):
        """
        Retrieves the temporary URL for the searched song from the storage.
        """
        # print(self.temporary_metadata_storage)
        return self.temporary_metadata_storage.get(self.song_user_searched)

    def _search_youtube_for_song(self):
        """
        Searches for the user-provided song on YouTube using YTMusic API.
        Returns song metadata from the search.
        """
        with YTMusic() as ytmusic:
            return ytmusic.search(self.song_user_searched, filter="songs", limit=1)[0]

    def search_from_youtube(self):
        """
        Searches for the user-provided song on YouTube using YTMusic API
        and extracts information such as title and webpage URL.
        """
        temp_url = self._get_temporary_url()
        # exit()

        if temp_url is None:
            song_metadata_from_yt = self._search_youtube_for_song()

            video_id = song_metadata_from_yt["videoId"]

            self.song_name_searched = song_metadata_from_yt["title"]
            self.song_url_searched = f"https://www.youtube.com/watch?v={video_id}"

            self._update_temporary_storage()

        else:
            # print(temp_url)
            self.song_name_searched = self.song_user_searched
            self.song_url_searched = temp_url
