"""
Downloads management screen for Aurras TUI.
"""

import os
import asyncio
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, Label
from textual.binding import Binding

from ..widgets.playlist import Playlist
from ...core.downloader import SongDownloader
from ...utils.path_manager import PathManager


class DownloadsScreen(Screen):
    """Screen for managing downloaded music."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("/", "focus_search", "Search"),
        Binding("p", "play_selected", "Play"),
        Binding("d", "delete_selected", "Delete"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        """Initialize the downloads screen."""
        super().__init__()
        self.path_manager = PathManager()
        self.downloaded_songs = []
        self.downloaded_playlists = []
        self.current_selection = None
        self.selection_type = None  # "song" or "playlist"
        self.is_downloading = False

    def compose(self) -> ComposeResult:
        """Compose the downloads screen layout."""
        yield Header()

        with Container(id="downloads-container"):
            yield Static(
                "Downloaded Music", id="downloads-title", classes="panel-title"
            )

            with Horizontal(id="downloads-search-panel"):
                yield Input(placeholder="Search downloads...", id="downloads-search")
                yield Button("New Download", id="new-download", variant="primary")

            with Horizontal(id="downloads-content"):
                # Left panel: downloaded playlists
                with Vertical(id="downloaded-playlists-container"):
                    yield Static("Downloaded Playlists", classes="list-title")
                    playlist_list = Playlist(
                        title="Playlists", id="downloaded-playlists"
                    )
                    yield playlist_list

                # Right panel: individual songs
                with Vertical(id="downloaded-songs-container"):
                    yield Static("Downloaded Songs", classes="list-title")
                    with ScrollableContainer(id="songs-container"):
                        songs_list = Playlist(title="Songs", id="downloaded-songs")
                        yield songs_list

            with Container(id="download-details"):
                yield Static("", id="selection-details")
                with Horizontal(id="download-progress", classes="hidden"):
                    yield Label("0%", id="progress-percent")
                    yield Static("Preparing download...", id="progress-status")

        with Horizontal(id="download-actions"):
            yield Button("Play", id="play-downloaded")
            yield Button("Delete", id="delete-downloaded")
            yield Button("Manage Storage", id="manage-storage")

        yield Footer()

    def on_mount(self):
        """Handle mounting of the downloads screen."""
        self.app.sub_title = "Download Management"
        self.run_worker(self._load_downloads())

    async def _load_downloads(self):
        """Load downloaded songs and playlists."""
        try:
            # Load downloaded songs
            songs_dir = self.path_manager.downloaded_songs_dir
            playlists_dir = self.path_manager.playlists_dir

            # Get downloaded songs
            self.downloaded_songs = []
            if songs_dir.exists():
                self.downloaded_songs = [
                    f
                    for f in os.listdir(songs_dir)
                    if not f.startswith(".")
                    and os.path.isfile(os.path.join(songs_dir, f))
                    and any(
                        f.endswith(ext)
                        for ext in [".mp3", ".wav", ".flac", ".ogg", ".m4a"]
                    )
                ]

            # Get downloaded playlists
            self.downloaded_playlists = []
            if playlists_dir.exists():
                self.downloaded_playlists = [
                    d
                    for d in os.listdir(playlists_dir)
                    if not d.startswith(".")
                    and os.path.isdir(os.path.join(playlists_dir, d))
                ]

            # Update the UI
            await self._update_downloads_ui()

        except Exception as e:
            self.notify(f"Error loading downloads: {e}")

    async def _update_downloads_ui(self):
        """Update the downloads UI with loaded data."""
        # Update songs list
        songs_list = self.query_one("#downloaded-songs", Playlist)
        songs_list.clear_options()

        for song in self.downloaded_songs:
            songs_list.append(song)

        # Update playlists list
        playlists_list = self.query_one("#downloaded-playlists", Playlist)
        playlists_list.clear_options()

        for playlist in self.downloaded_playlists:
            playlists_list.append(playlist)

        # Update status
        total_songs = len(self.downloaded_songs)
        total_playlists = len(self.downloaded_playlists)
        self.notify(f"Loaded {total_songs} songs and {total_playlists} playlists")

    def on_playlist_selected(self, event):
        """Handle playlist selection."""
        playlist_name = event.playlist.selected
        if playlist_name:
            self.current_selection = playlist_name
            self.selection_type = "playlist"
            self._update_selection_details()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "new-download":
            self._start_new_download()

        elif button_id == "play-downloaded":
            self.action_play_selected()

        elif button_id == "delete-downloaded":
            self.action_delete_selected()

        elif button_id == "manage-storage":
            self._manage_storage()

    def _start_new_download(self):
        """Start a new download."""
        if self.is_downloading:
            self.notify("A download is already in progress")
            return

        # Get the search box value
        search_input = self.query_one("#downloads-search", Input)
        query = search_input.value.strip()

        if not query:
            self.notify("Enter a song name to download")
            return

        self.is_downloading = True
        progress_container = self.query_one("#download-progress")
        progress_container.remove_class("hidden")
        progress_percent = self.query_one("#progress-percent", Label)
        progress_status = self.query_one("#progress-status", Static)

        # Start the download process
        async def download_async():
            try:
                progress_status.update("Searching for the song...")

                # Update progress in stages
                for i in range(1, 5):
                    await asyncio.sleep(0.5)
                    progress_percent.update(f"{i * 5}%")

                progress_status.update("Preparing download...")
                for i in range(5, 10):
                    await asyncio.sleep(0.5)
                    progress_percent.update(f"{i * 10}%")

                progress_status.update("Downloading...")
                for i in range(10, 20):
                    await asyncio.sleep(0.3)
                    progress_percent.update(f"{i * 5}%")

                # Simulate processing
                progress_status.update("Processing download...")
                await asyncio.sleep(1)
                progress_percent.update("100%")
                progress_status.update("Download complete!")

                # Add to downloaded songs
                self.downloaded_songs.append(f"{query}.mp3")
                await self._update_downloads_ui()

                # Hide progress after a delay
                await asyncio.sleep(2)
                progress_container.add_class("hidden")
                self.is_downloading = False

            except Exception as e:
                self.notify(f"Download error: {str(e)}")
                progress_container.add_class("hidden")
                self.is_downloading = False

        self.run_worker(download_async())

    def _update_selection_details(self):
        """Update the selection details panel."""
        details = self.query_one("#selection-details", Static)

        if not self.current_selection:
            details.update("")
            return

        if self.selection_type == "song":
            # Display song details
            song_path = self.path_manager.downloaded_songs_dir / self.current_selection
            if song_path.exists():
                size_kb = os.path.getsize(song_path) / 1024
                details.update(
                    f"Selected song: {self.current_selection}\nSize: {size_kb:.1f} KB"
                )
            else:
                details.update(
                    f"Selected song: {self.current_selection}\n(File not found)"
                )
        else:
            # Display playlist details
            playlist_path = self.path_manager.playlists_dir / self.current_selection
            if playlist_path.exists() and playlist_path.is_dir():
                song_count = len(list(playlist_path.glob("*.mp3")))
                details.update(
                    f"Selected playlist: {self.current_selection}\nSongs: {song_count}"
                )
            else:
                details.update(
                    f"Selected playlist: {self.current_selection}\n(Folder not found)"
                )

    def action_focus_search(self) -> None:
        """Focus the search input."""
        self.query_one("#downloads-search").focus()

    def action_refresh(self) -> None:
        """Refresh the downloads list."""
        self.run_worker(self._load_downloads())

    def action_play_selected(self) -> None:
        """Play the selected downloaded item."""
        songs_list = self.query_one("#downloaded-songs", Playlist)
        try:
            if songs_list.highlighted is not None:
                # Play selected song
                song_name = songs_list.get_option_at_index(
                    songs_list.highlighted
                ).prompt
                self.current_selection = song_name
                self.selection_type = "song"
                self._update_selection_details()

                song_path = self.path_manager.downloaded_songs_dir / song_name
                if not song_path.exists():
                    self.notify(f"Song file not found: {song_path}")
                    return

                self.notify(f"Playing downloaded song: {song_name}")
                return
        except Exception:
            pass

        # If no song selected, check if playlist is selected
        playlists_list = self.query_one("#downloaded-playlists", Playlist)
        try:
            if playlists_list.highlighted is not None:
                # Play selected playlist
                playlist_name = playlists_list.get_option_at_index(
                    playlists_list.highlighted
                ).prompt
                self.current_selection = playlist_name
                self.selection_type = "playlist"
                self._update_selection_details()
                self.notify(f"Playing playlist: {playlist_name}")
                return
        except Exception:
            pass

        self.notify("No download selected")

    def action_delete_selected(self) -> None:
        """Delete the selected download."""
        if not self.current_selection:
            self.notify("No item selected")
            return

        if self.selection_type == "song":
            self.notify(f"Deleting song: {self.current_selection}")
            # In a real implementation, we'd delete the file
            # and update the lists

            # Simulate deletion
            if self.current_selection in self.downloaded_songs:
                self.downloaded_songs.remove(self.current_selection)
                self.run_worker(self._update_downloads_ui())

        elif self.selection_type == "playlist":
            self.notify(f"Deleting playlist: {self.current_selection}")
            # In a real implementation, we'd delete the directory
            # and update the lists

            # Simulate deletion
            if self.current_selection in self.downloaded_playlists:
                self.downloaded_playlists.remove(self.current_selection)
                self.run_worker(self._update_downloads_ui())

    def _manage_storage(self):
        """Manage download storage."""
        songs_dir = self.path_manager.downloaded_songs_dir
        playlists_dir = self.path_manager.playlists_dir

        # Calculate storage used
        total_size = 0

        if songs_dir.exists():
            for file in songs_dir.glob("*.*"):
                if file.is_file():
                    total_size += file.stat().st_size

        if playlists_dir.exists():
            for dir_path in playlists_dir.glob("*/"):
                if dir_path.is_dir():
                    for file in dir_path.glob("*.*"):
                        if file.is_file():
                            total_size += file.stat().st_size

        # Convert to MB
        total_size_mb = total_size / (1024 * 1024)

        self.notify(f"Downloaded music is using {total_size_mb:.1f} MB of storage")
