"""
Playlist screen for Aurras TUI.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input

from ..widgets.playlist import Playlist


class PlaylistScreen(Screen):
    """Screen for displaying and managing playlists."""

    def compose(self) -> ComposeResult:
        """Compose the playlist screen layout."""
        yield Header()

        with Container(id="playlist-container"):
            with Vertical(id="playlist-controls"):
                yield Static(
                    "Your Playlists", id="playlists-title", classes="panel-title"
                )
                yield Input(placeholder="Search playlists...", id="playlist-search")

                with Horizontal(id="playlist-buttons"):
                    yield Button("New", id="new-playlist")
                    yield Button("Delete", id="delete-playlist")
                    yield Button("Import", id="import-playlist")

            with Horizontal(id="playlists-panel"):
                # Left panel: playlist list
                with Vertical(id="playlist-list-container"):
                    yield Static("Playlists", classes="list-title")
                    playlist_list = Playlist(title="My Playlists", id="playlist-list")
                    # Add some example playlists
                    for name in [
                        "Favorites",
                        "Rock Classics",
                        "Chill",
                        "Workout",
                        "Party",
                    ]:
                        playlist_list.append(name)
                    yield playlist_list

                # Right panel: songs in selected playlist
                with Vertical(id="playlist-songs-container"):
                    yield Static("Songs", classes="list-title")
                    playlist_songs = Playlist(title="Songs", id="playlist-songs")
                    yield playlist_songs

        with Horizontal(id="playlist-actions"):
            yield Button("Play", id="play-playlist")
            yield Button("Shuffle", id="shuffle-playlist")
            yield Button("Download", id="download-playlist")

        yield Footer()

    def on_mount(self):
        """Handle mounting of the playlist screen."""
        self.app.sub_title = "Playlist Management"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "play-playlist":
            self.notify("Playing playlist")
        elif button_id == "shuffle-playlist":
            self.notify("Shuffling playlist")
        elif button_id == "download-playlist":
            self.notify("Downloading playlist")
        elif button_id == "new-playlist":
            self.notify("Creating new playlist")
        elif button_id == "delete-playlist":
            self.notify("Deleting playlist")
        elif button_id == "import-playlist":
            self.notify("Importing playlist")
