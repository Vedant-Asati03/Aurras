"""
History Integration Module

This module provides functionality for integrating playback history with current song queues.
It handles retrieving history songs, creating combined playlists, and managing the transition
between history songs and searched songs.
"""

from collections import deque
from typing import List, Dict, Tuple

from aurras.utils.logger import get_logger
from aurras.services.youtube.search import SearchSong
from aurras.core.player.history import RecentlyPlayedManager

logger = get_logger("aurras.core.player.history_integration", log_to_console=False)


class HistoryIntegration:
    """
    Handles the integration of playback history with current song selections.

    This class provides functionality to create combined playlists with history songs
    and currently searched songs, with proper handling of transitions between them.

    Attributes:
        history_manager: Manager for retrieving recently played songs
        max_history_songs: Maximum number of history songs to include
        deduplicate: Whether to remove duplicate songs from history
    """

    def __init__(self, max_history_songs: int = 21, deduplicate: bool = True):
        """
        Initialize the history integration handler.

        Args:
            max_history_songs: Maximum number of history songs to include
            deduplicate: Whether to remove duplicate songs from history
        """
        self.history_manager = RecentlyPlayedManager()
        self.max_history_songs = max_history_songs
        self.deduplicate = deduplicate
        self._navigating_history = False
        self.history_cache = deque(maxlen=max_history_songs)
        logger.debug(f"History integration initialized (max_songs={max_history_songs})")

    def get_history_songs(self) -> List[Dict]:
        """
        Get recent history songs up to the specified limit.

        Returns:
            List of history song dictionaries with metadata
        """
        recent_history = self.history_manager.get_recent_songs(self.max_history_songs)

        history_deque = deque(reversed(recent_history), maxlen=self.max_history_songs)

        logger.debug(f"Retrieved {len(history_deque)} history songs")
        return list(history_deque)

    def get_history_song_names(self) -> List[str]:
        """
        Get list of history song names, optionally with deduplication.

        Returns:
            List of song names from history
        """
        recent_history = self.get_history_songs()

        history_songs = deque(maxlen=self.max_history_songs)
        for song in recent_history:
            song_name = song["song_name"]
            if not self.deduplicate or song_name not in history_songs:
                history_songs.append(song_name)

        return list(history_songs)

    def get_urls_for_history_songs(self, history_songs: List[str]) -> List[str]:
        """
        Find URLs for history songs by searching.

        Args:
            history_songs: List of song names to find URLs for

        Returns:
            List of URLs corresponding to the history songs
        """
        history_urls = []
        failed_songs = []

        for song_name in history_songs:
            # Create a fresh search for each song
            temp_search = SearchSong([song_name])
            temp_search.search_song(
                include_history=False
            )  # Don't include history to avoid recursion

            if temp_search.song_url_searched:
                history_urls.append(temp_search.song_url_searched[0])
            else:
                failed_songs.append(song_name)
                history_urls.append("null://")

        if failed_songs:
            logger.warning(
                f"Could not find URLs for {len(failed_songs)} history song(s)"
            )

        return history_urls

    def create_combined_playlist(
        self, searched_songs: List[str], searched_urls: List[str]
    ) -> Tuple[List[str], List[str], int]:
        """
        Create a combined playlist with history songs followed by searched songs.

        Args:
            searched_songs: List of song names from the current search
            searched_urls: List of URLs from the current search

        Returns:
            Tuple containing:
            - Combined list of song names (history + searched)
            - Combined list of URLs (history + searched)
            - Start index for searched songs (where history ends)
        """
        history_songs = self.get_history_song_names()

        if not history_songs:
            return searched_songs, searched_urls, 0

        history_urls = self.get_urls_for_history_songs(history_songs)

        all_songs = history_songs + searched_songs
        all_urls = history_urls + searched_urls
        start_index = len(history_songs)  # This is where the searched songs start

        logger.info(
            f"Created combined playlist: {len(all_songs)} songs (history: {len(history_songs)}, searched: {len(searched_songs)})"
        )
        return all_songs, all_urls, start_index

    # def display_history_info(self, history_songs: List[str]) -> None:
    #     """
    #     Display information about history songs in the console.

    #     Args:
    #         history_songs: List of history song names
    #     """
    #     if not history_songs:
    #         return

    # from aurras.utils.console.manager import console

    #     console.rule(f"[bold {theme.primary.hex}]Queue with History[/]", style=theme.secondary.hex)

    #     # Display info about history songs
    #     history_str = ", ".join(history_songs[: min(3, len(history_songs))])
    #     console.print(
    #         f"[{theme.dim}]Songs from history in queue ({len(history_songs)}): {history_str}...[/]"
    #     )

    def add_songs_to_history(self, songs: List[str], source: str = "online") -> None:
        """
        Add played songs to history.

        Args:
            songs: List of song names to add to history
            source: Source of the songs (e.g., 'online', 'playlist:name')
        """
        if getattr(self, "_navigating_history", False):
            logger.debug("Not adding songs to history while navigating history")
            return

        for song in songs:
            self.history_manager.add_to_history(song, source)

        logger.debug(f"Added {len(songs)} songs to history (source: {source})")

    def set_navigating_history(self, value: bool) -> None:
        """
        Set whether we're currently navigating through history.

        When navigating history, played songs won't be added to history again.

        Args:
            value: Whether we're navigating history
        """
        self._navigating_history = value
        logger.debug(f"Navigating history: {value}")

    def is_navigating_history(self) -> bool:
        """
        Check if we're currently navigating through history.

        Returns:
            Whether we're navigating history
        """
        return self._navigating_history


def integrate_history_with_playback(
    searched_songs: List[str], searched_urls: List[str], max_history_songs: int = 21
) -> Tuple[List[str], List[str], int]:
    """
    Utility function to integrate history with current search results.

    This is a convenience wrapper around HistoryIntegration for simple use cases.

    Args:
        searched_songs: List of song names from the current search
        searched_urls: List of URLs from the current search
        max_history_songs: Maximum number of history songs to include

    Returns:
        Tuple containing:
        - Combined list of song names (history + searched)
        - Combined list of URLs (history + searched)
        - Start index for searched songs (where history ends)
    """
    integration = HistoryIntegration(max_history_songs=max_history_songs)
    all_songs, all_urls, start_index = integration.create_combined_playlist(
        searched_songs, searched_urls
    )

    # integration.display_history_info(all_songs[:start_index])

    integration.add_songs_to_history(searched_songs)

    return all_songs, all_urls, start_index
