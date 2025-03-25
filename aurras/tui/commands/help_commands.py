"""
Help command provider for the command palette.
"""

from textual.command import Provider, Hit, DiscoveryHit
from rich.text import Text


class HelpProvider(Provider):
    """Provider that provides help options."""

    async def search(self, query: str):
        """Search for help topics matching the query."""
        # Only process queries that start with '?' prefix
        if not query.startswith("?"):
            return

        # Remove the prefix for matching
        query = query[1:].strip()

        # Help topics with descriptions and handlers
        help_topics = {
            "keyboard": (
                "Keyboard Shortcuts",
                "View all keyboard shortcuts",
                self._show_keyboard_shortcuts,
            ),
            "playback": (
                "Playback Controls",
                "How to control playback",
                self._show_playback_help,
            ),
            "search": (
                "Search Help",
                "How to search for music",
                self._show_search_help,
            ),
            "commands": ("Commands", "Available commands", self._show_commands_help),
            "spotify": (
                "Spotify Integration",
                "How to use Spotify features",
                self._show_spotify_help,
            ),
            "themes": (
                "Themes",
                "How to change the application theme",
                self._show_themes_help,
            ),
        }

        # If query is empty (just "?"), show all help topics
        if not query:
            for topic_id, (title, description, action) in help_topics.items():
                # Create a hit with no highlighting for each help topic
                yield Hit(
                    score=1.0,  # High score to show all topics
                    match_display=Text.from_markup(f"{title}: {description}"),
                    command=action,
                    text=title,
                    help=description,
                )
            return

        # Match against query
        matcher = self.matcher(query)

        for topic_id, (title, description, action) in help_topics.items():
            # Check various fields for matches
            topic_score = matcher.match(topic_id)
            title_score = matcher.match(title)
            desc_score = matcher.match(description)
            score = max(topic_score, title_score, desc_score)

            if score > 0:
                # Create display text with highlighting
                display = matcher.highlight(f"{title}: {description}")

                # Create hit
                yield Hit(
                    score=score,
                    match_display=display,
                    command=action,
                    text=title,
                    help=description,
                )

    async def discover(self):
        """Return discovery help topics."""
        # Return empty to hide help options from initial view
        # Only show help options when '?' is typed
        return

    # Help topic handlers
    def _show_keyboard_shortcuts(self):
        self.app.notify("Keyboard shortcuts: Space=Play/Pause, b=Next, n=Previous")

    def _show_playback_help(self):
        self.app.notify("Playback Controls: Space=Play/Pause, b=Next, n=Previous")

    def _show_search_help(self):
        self.app.notify("Search: Type a song name or artist to search")

    def _show_commands_help(self):
        self.app.notify("Commands: Type > followed by a command name")

    def _show_spotify_help(self):
        self.app.notify("Spotify: Setup required, see settings")

    def _show_themes_help(self):
        self.app.notify(
            "Themes: Type >theme_NAME to change the theme. Available themes: galaxy, aurora, sunset, monochrome, paper, cyberpunk, ember, midnight, carbon"
        )
