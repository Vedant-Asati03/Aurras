"""
Song search provider for the command palette.
"""

import asyncio
from typing import Callable

from textual.command import Provider, Hit, DiscoveryHit
from rich.text import Text

from ...player.online import SongStreamHandler
from ...services.youtube.search import SearchSong
from ...core.cache.search_db import SearchFromSongDataBase


class SongSearchProvider(Provider):
    """Provider that searches for songs and returns them as commands."""

    def __init__(self, screen, match_style=None):
        """Initialize the song search provider."""
        super().__init__(screen, match_style)
        self.search_db = SearchFromSongDataBase()
        self.is_searching = False
        self.song_name = ""
        self.song_url = ""

    async def search(self, query: str):
        """Search for songs matching the query."""
        # Only handle queries without a prefix (song searches)
        if query.startswith(">") or query.startswith("?"):
            return

        # Skip short queries to avoid excessive searching
        if not query or len(query.strip()) < 2:
            return

        # Set searching flag to avoid multiple concurrent searches
        if self.is_searching:
            return

        self.is_searching = True

        try:
            # First check history for matches
            history_results = await self._get_history_results(query)
            for hit in history_results:
                yield hit

            # Actual search through the YouTube API
            matcher = self.matcher(query)

            # Search for the song using our existing search implementation
            def search_thread():
                try:
                    search = SearchSong(query)
                    search.search_song()
                    return (search.song_name_searched, search.song_url_searched)
                except Exception as e:
                    return (f"Error: {str(e)}", "")

            # Run the search in a thread to avoid blocking
            self.song_name, self.song_url = await asyncio.to_thread(search_thread)

            # Add the main search result at the top if valid
            if not self.song_name.startswith("Error:"):
                # Calculate match score
                score = matcher.match(self.song_name)

                # Create the display text with highlighted matches
                display = matcher.highlight(self.song_name)

                # Create a hit with the song data
                yield Hit(
                    score=score,
                    match_display=display,
                    command=self._create_play_callback(self.song_name, self.song_url),
                    text=self.song_name,
                    help="Play this song",
                )

            # Add suggestions based on query
            suggestions = await self._get_suggestions(query, matcher)
            for hit in suggestions:
                yield hit

        finally:
            self.is_searching = False

    async def discover(self):
        """Return discovery hits (shown before user input)."""
        # Get recently played songs
        try:
            song_dict = self.search_db.initialize_song_dict()

            for i, (user_searched, (song_name, song_url)) in enumerate(
                song_dict.items()
            ):
                if i >= 5:  # Limit to 5 recent songs
                    break

                display = Text.from_markup(
                    f"[italic]{song_name}[/italic] [dim](Recent)[/dim]"
                )
                yield DiscoveryHit(
                    display=display,
                    command=self._create_play_callback(song_name, song_url),
                    text=song_name,
                    help="Recent song",
                )

        except Exception:
            pass  # Return empty if history can't be accessed

    async def _get_history_results(self, query: str) -> list:
        """Get matching results from search history."""
        results = []
        try:
            # Create matcher for scoring
            matcher = self.matcher(query)

            # Get search history
            song_dict = self.search_db.initialize_song_dict()

            # Filter and score results
            for user_searched, (song_name, song_url) in song_dict.items():
                # Check if query matches user's search or song name
                if (
                    query.lower() in user_searched.lower()
                    or query.lower() in song_name.lower()
                ):
                    # Calculate match score
                    search_score = matcher.match(user_searched)
                    name_score = matcher.match(song_name)
                    score = max(search_score, name_score)

                    # Create the display text with highlighted matches
                    display = matcher.highlight(f"{song_name} (History)")

                    # Create a hit with the song data
                    hit = Hit(
                        score=score,
                        match_display=display,
                        command=self._create_play_callback(song_name, song_url),
                        text=song_name,
                        help="From your history",
                    )
                    results.append(hit)

                    # Limit to 3 history results
                    if len(results) >= 3:
                        break

        except Exception:
            pass  # Silently fail if history can't be accessed

        return results

    async def _get_suggestions(self, query: str, matcher):
        """Get additional suggestions based on the query."""
        suggestions = []

        if len(query) > 1:
            suggestion_texts = [
                f"{query} Remix",
                f"{query} Acoustic",
                f"{query} Live",
                f"Best of {query}",
            ]

            for suggestion in suggestion_texts:
                # Calculate match score - suggestions should have lower scores
                score = matcher.match(suggestion) * 0.8  # Lower priority

                # Create the display text
                display = matcher.highlight(f"{suggestion} (Suggestion)")

                # Create a hit with the suggestion
                hit = Hit(
                    score=score,
                    match_display=display,
                    command=self._create_play_callback(suggestion),
                    text=suggestion,
                    help="Suggested search",
                )
                suggestions.append(hit)

        return suggestions

    def _create_play_callback(self, song_name: str, song_url: str = "") -> Callable:
        """Create a callback function to play the selected song."""

        def play_song():
            # Update the app with current song
            if hasattr(self.app, "current_song"):
                self.app.current_song = song_name

            # Show notification
            self.app.notify(f"Playing: {song_name}")

            # Update player screen if possible
            player_screen = self.app.screen
            if hasattr(player_screen, "_update_song_info"):
                player_screen._update_song_info(song_name)

            # Play the song in a worker
            async def play_async():
                try:
                    # Play the song in a background thread
                    await asyncio.to_thread(
                        lambda: SongStreamHandler(song_name).listen_song_online()
                    )
                except Exception as e:
                    self.app.notify(f"Playback error: {str(e)}")

            # Run the playback worker
            self.app.run_worker(play_async())

        return play_song
