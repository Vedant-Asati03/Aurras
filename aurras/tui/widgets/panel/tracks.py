"""
Track panel widget for Aurras TUI.
"""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import SelectionList, OptionList

from ....player.queue import QueueManager
from ....player.history import RecentlyPlayedManager
from ..icon import Icon
from ..empty import Empty


class QueuePanel(SelectionList):
    """Queue list widget showing upcoming songs."""

    def __init__(self, *args, **kwargs):
        """Initialize queue with border title."""
        super().__init__(*args, **kwargs)
        self.border_title = "²queue"
        self.queue_manager = QueueManager()

    def on_mount(self):
        """Add current queue items on mount."""
        self._refresh_queue()
        # Register a callback to update when queue changes
        self.queue_manager.register_change_callback(self._refresh_queue)

    def _refresh_queue(self):
        """Refresh queue items from queue manager."""
        # Clear options safely
        self.clear_options()

        queue_items = self.queue_manager.get_queue()

        if not queue_items:
            # Show empty state - Fix: Pass as single tuple argument
            self.add_option(("Queue is empty", "empty"))
            return

        # Add actual queue items
        for i, song in enumerate(queue_items):
            song_id = f"queue_{i}"
            # Fix: Pass as single tuple argument
            self.add_option((song, song_id))

    def add_song(self, title, artist, duration, song_id=None):
        """Add a song to the queue."""
        if song_id is None:
            song_id = f"{title}_{artist}".lower().replace(" ", "_")

        display_text = f"{title} - {artist} [{duration}]"
        # Fix: Pass as single tuple argument
        self.add_option((display_text, song_id))

    def clear_options(self):
        """Clear all options in the selection list safely."""
        # The safest way to clear options is to create a new empty list
        self.options.clear()


class RecentsPanel(OptionList):
    """Recently played list widget showing previously played songs."""

    def __init__(self, *args, **kwargs):
        """Initialize with border title."""
        super().__init__(*args, **kwargs)
        self.border_title = "³recents"
        self.history_manager = RecentlyPlayedManager()

    def compose(self) -> ComposeResult:
        """Compose the recents panel contents."""
        if not self._load_recents():
            yield Empty("No playback history!")
            return
        self.add_options(self._load_recents())

    def on_mount(self):
        """Add recent history items on mount."""
        self._refresh_history()

    def _refresh_history(self):
        """Refresh history items from history manager."""
        self._clear_options()

    def _load_recents(self):
        """Load recently played songs into the panel."""
        recents = self.history_manager.get_recent_songs()
        return [f"{Icon.PRIMARY('')} {item['song_name']}" for item in recents]

    def _clear_options(self):
        """Clear all options from the option list."""
        recents = []


class TrackPanel(Vertical):
    """Container widget for right panel components (queue and history)."""

    def __init__(self, *args, **kwargs):
        """Initialize the right panel."""
        # Extract border_subtitle if present before passing to parent
        border_subtitle = kwargs.pop("border_subtitle", None)
        super().__init__(*args, **kwargs)
        self.border_title = "Tracks"

        # Apply border_subtitle if provided
        if border_subtitle:
            self.border_subtitle = border_subtitle

    def compose(self):
        """Compose the right panel contents."""
        queue_container = QueuePanel(id="song-queue")
        queue_container.border_title = "³queue"
        yield queue_container

        recents_container = RecentsPanel(id="recently-played")
        recents_container.border_title = "⁴recents"
        yield recents_container
