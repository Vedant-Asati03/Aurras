"""
Playlist widget for Aurras TUI.
"""

from textual.widgets import SelectionList


class Playlist(SelectionList):
    """Playlist widget displaying songs in a playlist."""

    DEFAULT_CSS = """
    Playlist {
        height: 1fr;
        border: solid $primary-darken-2;
        border-title-align: center;
    }
    """

    def __init__(self, title="Playlist", *args, **kwargs):
        """Initialize a playlist widget."""
        super().__init__(*args, **kwargs)
        self.border_title = title

    def append(self, option):
        """Add an item to the playlist."""
        # If it's a string, convert it to an option tuple
        if isinstance(option, str):
            # Fix: Pass as single tuple argument
            self.add_option((option, option.lower().replace(" ", "_")))
        else:
            self.add_option(option)
