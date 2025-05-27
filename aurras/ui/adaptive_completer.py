"""
Search Bar Module

This module provides the DynamicSearchBar class which uses a registry pattern
to route input to the appropriate completer based on patterns.
"""

from prompt_toolkit.completion import Completer

from aurras.core.settings import SETTINGS
from aurras.ui.core.registry.completer import CompleterRegistry
from aurras.ui.completer import (
    SongCompleter,
    PlaylistCompleter,
    FeatureCompleter,
    CommandCompleter,
)


class AdaptiveCompleter(Completer):
    """
    Dynamic search bar that selects the appropriate completer based on input patterns.

    Uses a registry-based approach to route input to specialized completers.
    """

    def __init__(self):
        """Initialize the DynamicSearchBar with registered completers."""
        self.registry = CompleterRegistry()

        self.song_completer = SongCompleter()
        self.command_completer = CommandCompleter()
        self.feature_completer = FeatureCompleter()
        self.playlist_completer = PlaylistCompleter()

        # Register completers with appropriate prefixes/patterns
        self.registry.register_prefix(SETTINGS.command_palette_key, self.command_completer)
        self.registry.register_prefix(SETTINGS.options_menu_key, self.feature_completer)
        self.registry.register_pattern(r"^(p|d),", self.playlist_completer)

        # Set default completer for when no pattern matches
        self.registry.set_default_completer(self.song_completer)

    def get_completions(self, document, complete_event):
        """
        Get completions from the appropriate completer based on the input.

        Args:
            document: The document containing the input text
            complete_event: The completion event

        Returns:
            Completions from the selected completer
        """
        text_before_cursor = document.text_before_cursor.lower()

        completer = self.registry.get_completer_for_input(text_before_cursor)

        # Delegate to the selected completer
        return completer.get_completions(document, complete_event)
