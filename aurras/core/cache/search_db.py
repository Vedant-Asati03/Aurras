from .loader import LoadSongHistoryData


class SearchFromSongDataBase:
    def __init__(self):
        """
        Initializes the SearchSong class with the user-provided song name.

        Args:
            song_user_searched (str): The name of the song provided by the user.
        """
        self.load_song_metadata = LoadSongHistoryData()

    def initialize_song_dict(self):
        song_metadata_from_db = self.load_song_metadata.load_song_metadata_from_db()
        song_dict = {
            song_user_searched: (song_name_searched, song_url_searched)
            for song_user_searched, song_name_searched, song_url_searched in song_metadata_from_db
        }

        return song_dict