from typing import List, Tuple

from aurras.ui.completer.base import BaseCompleter
from aurras.services.youtube.search import SearchFromYoutube


class SongCompleter(BaseCompleter):
    """
    Auto-completion class for song search.

    Uses YouTube search to provide song suggestions.
    """

    def __init__(self):
        """
        Initializes the SongCompleter class.
        """
        self.song_recommendation = None

    def get_suggestions(self, text: str) -> List[Tuple[str, str]]:
        """
        Get song suggestions based on YouTube search.

        Args:
            text: The text to search for

        Returns:
            List of tuples (song_name, "") - descriptions empty for songs
        """
        song_name_typing = text.lstrip()

        if song_name_typing == "":
            return []

        search_song = SearchFromYoutube([song_name_typing])
        try:
            search_song.search_from_youtube()
            self.song_recommendation = search_song.song_name_searched
        except Exception:
            return []

        if self.song_recommendation:
            return [(song, "") for song in self.song_recommendation]
        return []
