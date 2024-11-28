from libs.manage_cache.update_cache import UpdateSearchHistoryDatabase
from libs.manage_song_searches.handle_song_searches.song_metadata import SongMetaData
from libs.manage_song_searches.handle_song_searches.search_on_youtube import (
    SearchFromYoutube,
)
from libs.manage_song_searches.handle_song_searches.search_from_db import (
    SearchFromSongDataBase,
)


class SearchSong:
    def __init__(self, song_user_searched) -> None:
        self.song_metadata = SongMetaData()
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
                self.song_metadata.song_name_searched,
                self.song_metadata.song_url_searched,
            ) = song_dict[self.song_user_searched]

        else:
            self.search_from_yt.search_from_youtube()

            self.song_metadata.song_name_searched = (
                self.search_from_yt.song_metadata.song_name_searched
            )
            self.song_metadata.song_url_searched = (
                self.search_from_yt.song_metadata.song_url_searched
            )

            self.update_song_history.save_to_cache(
                self.song_user_searched,
                self.search_from_yt.song_metadata.song_name_searched,
                self.search_from_yt.song_metadata.song_url_searched,
            )
