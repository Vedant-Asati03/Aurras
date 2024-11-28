from ytmusicapi import YTMusic
from libs.manage_song_searches.handle_song_searches.song_metadata import SongMetaData


temporary_metadata_storage = {}


class SearchFromYoutube:
    def __init__(self, song_user_searched) -> None:
        super().__init__()
        self.song_metadata = SongMetaData()
        self.song_user_searched = song_user_searched

    def _get_temporary_url(self):
        """
        Retrieves the temporary URL for the searched song from the storage.
        """
        return temporary_metadata_storage.get(self.song_user_searched)

    def _update_temporary_storage(self):
        """
        Updates the temporary storage with the song name and its URL.
        """
        temporary_metadata_storage.update(
            {
                self.song_metadata.song_name_searched: self.song_metadata.song_url_searched
            }
        )

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

        if temp_url is None:
            song_metadata_from_yt = self._search_youtube_for_song()

            video_id = song_metadata_from_yt["videoId"]

            self.song_metadata.song_name_searched = song_metadata_from_yt["title"]
            self.song_metadata.song_url_searched = (
                f"https://www.youtube.com/watch?v={video_id}"
            )

            self._update_temporary_storage()

        else:
            self.song_metadata.song_name_searched = self.song_user_searched
            self.song_metadata.song_url_searched = temp_url
