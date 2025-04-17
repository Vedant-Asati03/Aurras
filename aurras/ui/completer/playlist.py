from typing import List, Tuple

from .base import BaseCompleter
from ...playlist.manager import PlaylistManager


class PlaylistCompleter(BaseCompleter):
    """
    Auto-completion class for playlists.

    Provides suggestions from available playlists.
    """

    def __init__(self):
        """
        Initializes the SuggestPlaylists class.
        """
        self.playlist_manager = PlaylistManager()

    def get_suggestions(self, text: str) -> List[Tuple[str, str]]:
        """
        Get playlist suggestions.

        Args:
            text: The input text with prefix

        Returns:
            List of tuples (playlist_name, "Playlist")
        """
        all_playlists: List[str] = list(
            self.playlist_manager.get_all_playlists().keys()
        )

        if not all_playlists:
            return []

        if text.startswith("p,") or text.startswith("d,"):
            # Return all playlists with a "Playlist" description
            return [(playlist, "Playlist") for playlist in all_playlists]

        return []
