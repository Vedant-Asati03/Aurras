"""
Main player screen for Aurras TUI.
"""

import asyncio
import traceback
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Static, Label, ProgressBar, Button
from textual.events import Click
from textual import on
from textual.binding import Binding
from textual.widgets import OptionList

from ..widgets.panel.library import LibraryPanel
from ..widgets.panel.tracks import TrackPanel
from ...player.online import ListenSongOnline
from ...services.lyrics import LyricsFetcher
from ...utils.path_manager import PathManager


class HomeScreen(Screen):
    """Main player screen with playback controls and queue."""

    BINDINGS = [
        Binding("1", "toggle_playlists_panel", "Toggle Playlists", False),
        Binding("2", "toggle_tracks_panel", "Toggle Tracks", False),
        Binding("3", "toggle_queue_panel", "Toggle Queue", False),
        Binding("4", "toggle_recents_panel", "Toggle Recents", False),
        Binding("5", "toggle_lyrics_size", "Toggle Lyrics", False),
    ]

    def __init__(self):
        """Initialize the player screen."""
        super().__init__()
        self.current_song = None
        self.lyrics_fetcher = None
        self.lyrics_expanded = False
        self.playlists_visible = True
        self.tracks_visible = True
        self.library_visible = True
        self.queue_visible = True
        self.recents_visible = True
        self.path_manager = PathManager()

    def compose(self) -> ComposeResult:
        """Compose the player screen layout."""
        with Horizontal(id="main-container"):
            yield LibraryPanel(id="left-panel")

            player = Vertical(id="player-panel")
            player.border_title = "AURRAS"
            with player:
                song_info = Horizontal(id="song-info")
                song_info.border_title = "player"
                with song_info:
                    song_name = Container(id="song-name")
                    with song_name:
                        yield Label("Song Title", id="song-title")
                        yield Label("Artist - Album", id="song-details")

                    cover = Container(id="cover-container", classes="bordered")
                    with cover:
                        yield Label("Cover Image", id="cover-image")

                lyrics_preview = Container(
                    id="lyrics-preview", classes="bordered lyrics-normal"
                )
                lyrics_preview.border_title = "⁵lyrics"
                lyrics_preview.border_subtitle = "~vol 100"
                with lyrics_preview:
                    yield Static(
                        "No song playing...",
                        id="lyrics-text",
                    )

                with Horizontal(id="info-control-container"):
                    with Horizontal(id="progress-info"):
                        yield Static("00:00", id="time-elapsed")
                        yield ProgressBar(
                            total=100, id="song-progress", show_percentage=False
                        )
                        yield Static("3:45", id="time-total")

            yield TrackPanel(border_subtitle="v1.1.1", id="right-panel")

        yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        """Handle the screen mount event."""
        self.set_interval(0.5, self._update_progress)

        progress_bar = self.query_one("#song-progress", ProgressBar)
        progress_bar.value = 30

        # Setup update timers for queue and history
        self.set_interval(5, self._refresh_displays)

        # Note: We no longer need to call _load_library_content() here
        # since the LibraryPanel widget will load its content when mounted

    def _update_progress(self) -> None:
        """Update the song progress."""
        progress_bar = self.query_one("#song-progress")
        if progress_bar.value < progress_bar.total:
            progress_bar.advance(1)
        else:
            progress_bar.value = 0

    def _refresh_displays(self) -> None:
        """Refresh the queue and history displays."""
        try:
            queue = self.query_one("#song-queue")
            queue._refresh_queue()

            recents = self.query_one("#recently-played")
            recents._refresh_history()
        except Exception as e:
            self.notify(f"Error refreshing displays: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "show-lyrics":
            # Show lyrics screen for current song
            if self.current_song:
                self.app.open_lyrics_screen(self.current_song)
            else:
                self.notify("No song playing")
        elif event.button.id == "play-pause":
            self.app.action_toggle_play()
        elif event.button.id == "previous":
            self.app.action_previous_song()
        elif event.button.id == "stop":
            # Stop playback
            self.notify("Playback stopped")

    def on_label_click(self, event: Click) -> None:
        """Handle label click events for navigation."""
        # Check if the click target is a Label
        if isinstance(event.target, Label):
            label_id = event.target.id

            if label_id == "nav-playlists":
                self.app.push_screen("playlists")
            elif label_id == "nav-downloads":
                self.app.push_screen("downloads")
            elif label_id == "nav-settings":
                self.app.push_screen("settings")

    def on_selection_list_selected(self, event):
        """Handle selection from song lists."""
        source_id = event.selection_list.id
        selection = event.selection_list.selected

        if source_id == "song-queue" and selection and selection != "empty":
            self.notify(f"Selected song from queue: {selection}")
            # Here you could implement logic to jump to this song in the queue

    def on_option_list_selected(self, event):
        """Handle selection from recently played list."""
        if event.option_list.id == "recently-played":
            # Get the highlighted song
            song_index = event.option_list.highlighted
            if song_index is not None:
                song_option = event.option_list.get_option_at_index(song_index)
                song_name = song_option.prompt

                # Show notification
                self.notify(f"Playing from history: {song_name}")

                # Start playback in a worker thread to avoid blocking the UI
                def play_song():
                    try:
                        player = ListenSongOnline(song_name)
                        player.listen_song_online()
                    except Exception as e:
                        self.notify(f"Error playing song: {str(e)}")

                # Run the playback in a worker to avoid blocking UI
                self.run_worker(play_song)

    def on_option_list_click(self, event):
        """Handle click events on option lists (like recently played)."""
        if event.option_list.id == "recently-played":
            # Get the clicked item's index
            try:
                # Use highlighted item as the clicked item
                song_index = event.option_list.highlighted
                if song_index is not None:
                    song_option = event.option_list.get_option_at_index(song_index)
                    song_name = song_option.prompt

                    # Show notification
                    self.notify(f"Playing from history: {song_name}")

                    # Start playback in a worker thread
                    def play_song():
                        try:
                            player = ListenSongOnline(song_name)
                            player.listen_song_online()
                        except Exception as e:
                            self.notify(f"Error playing song: {str(e)}")

                    # Run the playback in a worker
                    self.run_worker(play_song)
            except Exception as e:
                self.notify(f"Error: {str(e)}")

    # Fix the event handler using the proper decorator syntax for Textual
    @on(OptionList.OptionSelected)
    def handle_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option list selection."""
        if event.option_list.id == "recently-played":
            song_name = event.option.prompt

            # Show notification
            self.notify(f"Starting playback: {song_name}")

            # Update the song info and lyrics immediately
            self._update_song_info(song_name)

            # Start playback in a worker thread to avoid blocking the UI
            async def play_song_async():
                try:
                    # Create a verbose notification to track progress
                    self.notify("Creating player instance...")

                    # Run the synchronous player in a thread to avoid blocking
                    await asyncio.to_thread(self._play_song, song_name)

                except Exception as e:
                    self.notify(f"Error playing song: {str(e)}")

            # Run the playback in a worker with an async function
            self.run_worker(play_song_async)

    def _play_song(self, song_name):
        """Play a song using the player (synchronous function)."""
        try:
            player = ListenSongOnline(song_name)
            player.listen_song_online()
        except Exception as e:
            # This exception will be caught in the async wrapper
            raise e

    def _update_song_info(self, song_name):
        """Update the song info and lyrics display."""
        self.current_song = song_name

        # Update song title
        song_title = self.query_one("#song-title", Label)
        song_title.update(song_name)

        # Update song details (placeholder for now)
        song_details = self.query_one("#song-details", Label)
        song_details.update("Now Playing")

        # Update lyrics
        self._fetch_and_update_lyrics(song_name)

    def _fetch_and_update_lyrics(self, song_name):
        """Fetch lyrics for the current song and update the display."""

        # Create a worker to fetch lyrics asynchronously
        async def fetch_lyrics_async():
            try:
                # Show loading message
                lyrics_text = self.query_one("#lyrics-text", Static)
                lyrics_text.update("Fetching lyrics...")

                # Update the lyrics container title to show which song we're getting lyrics for
                lyrics_container = self.query_one("#lyrics-preview", Container)
                lyrics_container.border_title = f"@lyrics: {song_name}"

                # Create lyrics fetcher in a thread to avoid blocking
                self.notify("Creating lyrics fetcher...")
                self.lyrics_fetcher = LyricsFetcher(song_name)

                # Run the synchronous lyrics fetch in a thread with additional debugging
                self.notify("Fetching lyrics, please wait...")

                # Define a function that will run in a separate thread
                def fetch_lyrics_thread():
                    try:
                        # Call the fetch_lyrics method
                        self.lyrics_fetcher.fetch_lyrics()
                        # Return the lyrics
                        return self.lyrics_fetcher.lyrics
                    except Exception as e:
                        # Capture any exceptions with full traceback
                        return f"Error: {str(e)}\n{traceback.format_exc()}"

                # Run the function in a thread and get the result
                lyrics_result = await asyncio.to_thread(fetch_lyrics_thread)

                # Process the result
                if isinstance(lyrics_result, str) and lyrics_result.startswith(
                    "Error:"
                ):
                    # We got an error
                    self.notify(f"Error in lyrics thread: {lyrics_result[:100]}...")
                    lyrics_text.update(
                        f"Failed to fetch lyrics: {lyrics_result[:100]}..."
                    )
                else:
                    # Update the lyrics display based on the result
                    if self.lyrics_fetcher and self.lyrics_fetcher.lyrics:
                        try:
                            # Format the lyrics for better display in the TUI
                            formatted_lyrics = self._format_lyrics_for_display(
                                self.lyrics_fetcher.lyrics
                            )
                            lyrics_text.update(formatted_lyrics)
                            self.notify("Lyrics updated successfully")
                        except Exception as e:
                            self.notify(f"Error formatting lyrics: {str(e)}")
                            lyrics_text.update(
                                "Error formatting lyrics. Raw text may contain special characters."
                            )
                    else:
                        lyrics_text.update("No lyrics found for this song.")
                        self.notify("No lyrics found for this song")

            except Exception as e:
                error_msg = f"Error fetching lyrics: {str(e)}"
                self.notify(error_msg)
                lyrics_text = self.query_one("#lyrics-text", Static)
                lyrics_text.update(f"Failed to load lyrics.\nError: {str(e)}")

        # Run the async function in a worker
        self.run_worker(fetch_lyrics_async)

    def _format_lyrics_for_display(self, lyrics):
        """Format lyrics for better display in the TUI."""
        if not lyrics:
            return "No lyrics available"

        try:
            # Limit the length to prevent performance issues with very long lyrics
            max_length = 2000
            if len(lyrics) > max_length:
                lyrics = (
                    lyrics[:max_length] + "\n\n[...lyrics truncated due to length...]"
                )

            # Strip all potential Rich markup characters completely
            # This is a more aggressive approach than escaping
            import re

            # First replace any escape sequences and block out all potential markup characters
            sanitized_lyrics = re.sub(
                r"\[|\]|\{|\}|\<|\>|\*|\_|\`|\||\$|\&|\!|\@|\#|\%|\^|\~", " ", lyrics
            )

            # Replace any Rich escape sequences
            sanitized_lyrics = sanitized_lyrics.replace("\\", "")

            # Make sure there are line breaks for readability
            if "\n" not in sanitized_lyrics[:100]:
                # If no line breaks in the first part, try to add some
                words = sanitized_lyrics.split(" ")
                lines = []
                current_line = []

                for word in words:
                    if not word:
                        continue
                    current_line.append(word)
                    if len(" ".join(current_line)) > 40:  # Line length of ~40 chars
                        lines.append(" ".join(current_line))
                        current_line = []

                if current_line:  # Add the last line if there is one
                    lines.append(" ".join(current_line))

                sanitized_lyrics = "\n".join(lines)

            # Use a completely plain text representation without any styling
            self.notify("Lyrics formatted successfully")
            return sanitized_lyrics

        except Exception as e:
            # Last resort - ultra-safe version that just keeps alphanumeric and basic punctuation
            self.notify(f"Using fallback lyrics formatting: {str(e)}")
            import re

            # Only keep alphanumeric characters and basic punctuation
            ultra_safe = re.sub(r"[^\w\s\.\,\;\:\'\"\!\?]", "", lyrics)
            return ultra_safe

    def action_toggle_lyrics_size(self) -> None:
        """Toggle the size of the lyrics container."""
        lyrics_container = self.query_one("#lyrics-preview", Container)
        song_info = self.query_one("#song-info", Horizontal)

        # Toggle between expanded and normal size
        self.lyrics_expanded = not self.lyrics_expanded

        if self.lyrics_expanded:
            lyrics_container.styles.height = "90vh"  # Increase height
            song_info.styles.display = "none"
        else:
            lyrics_container.styles.height = "25vh"  # Original height
            song_info.styles.display = "block"

    def action_toggle_playlists_panel(self) -> None:
        """Toggle visibility of the playlists panel."""
        playlists_container = self.query_one("#playlists-container", VerticalScroll)
        tracks_container = self.query_one("#tracks-container", OptionList)

        self.playlists_visible = not self.playlists_visible

        if self.playlists_visible:
            playlists_container.styles.display = "block"
            # Adjust heights based on tracks visibility
            if self.tracks_visible:
                playlists_container.styles.height = "50%"
                tracks_container.styles.height = "50%"
            else:
                playlists_container.styles.height = "100%"
        else:
            playlists_container.styles.display = "none"
            if self.tracks_visible:
                tracks_container.styles.height = "100%"

        # Update overall layout if both panels are hidden
        if not self.playlists_visible and not self.tracks_visible:
            self.library_visible = False
        else:
            self.library_visible = True

        self._update_main_layout()

    def action_toggle_tracks_panel(self) -> None:
        """Toggle visibility of the tracks panel."""
        playlists_container = self.query_one("#playlists-container", VerticalScroll)
        tracks_container = self.query_one("#tracks-container", OptionList)

        self.tracks_visible = not self.tracks_visible

        if self.tracks_visible:
            tracks_container.styles.display = "block"
            # Adjust heights based on playlists visibility
            if self.playlists_visible:
                playlists_container.styles.height = "50%"
                tracks_container.styles.height = "50%"
            else:
                tracks_container.styles.height = "100%"
        else:
            tracks_container.styles.display = "none"
            if self.playlists_visible:
                playlists_container.styles.height = "100%"

        # Update overall layout if both panels are hidden
        if not self.playlists_visible and not self.tracks_visible:
            self.library_visible = False
        else:
            self.library_visible = True

        self._update_main_layout()

    # Update the existing toggle methods to use the new container layout
    def action_toggle_queue_panel(self) -> None:
        """Toggle visibility of the queue panel."""
        right_panel = self.query_one("#right-panel", Vertical)
        queue_panel = self.query_one("#song-queue")
        recents_panel = self.query_one("#recently-played")

        self.queue_visible = not self.queue_visible

        if self.queue_visible:
            queue_panel.styles.display = "block"
            # Adjust heights based on recents visibility
            if self.recents_visible:
                queue_panel.styles.height = "60%"
                recents_panel.styles.height = "40%"
            else:
                queue_panel.styles.height = "100%"
        else:
            queue_panel.styles.display = "none"
            if self.recents_visible:
                recents_panel.styles.height = "100%"

        # Check if both queue and recents are hidden
        if not self.queue_visible and not self.recents_visible:
            right_panel.styles.display = "none"
        else:
            right_panel.styles.display = "block"

        self._update_main_layout()

    def action_toggle_recents_panel(self) -> None:
        """Toggle visibility of the recently played panel."""
        right_panel = self.query_one("#right-panel", Vertical)
        queue_panel = self.query_one("#song-queue")
        recents_panel = self.query_one("#recently-played")

        self.recents_visible = not self.recents_visible

        if self.recents_visible:
            recents_panel.styles.display = "block"
            # Adjust heights based on queue visibility
            if self.queue_visible:
                queue_panel.styles.height = "60%"
                recents_panel.styles.height = "40%"
            else:
                recents_panel.styles.height = "100%"
        else:
            recents_panel.styles.display = "none"
            if self.queue_visible:
                queue_panel.styles.height = "100%"

        # Check if both queue and recents are hidden
        if not self.queue_visible and not self.recents_visible:
            right_panel.styles.display = "none"
        else:
            right_panel.styles.display = "block"

        self._update_main_layout()

    def _update_main_layout(self) -> None:
        """Update the main layout based on which panels are visible."""
        main_panel = self.query_one("#main-container", Horizontal)
        left_panel = self.query_one("#left-panel", Vertical)
        right_panel = self.query_one("#right-panel", Vertical)

        # Determine left panel visibility based on children
        if not self.playlists_visible and not self.tracks_visible:
            left_panel.styles.display = "none"
            self.library_visible = False
        else:
            left_panel.styles.display = "block"
            self.library_visible = True

        # Determine right panel visibility
        right_visible = self.queue_visible or self.recents_visible

        # Update grid based on visibility
        if self.library_visible and right_visible:
            main_panel.styles.grid_size_columns = 3
            main_panel.styles.grid_columns = "1fr 3fr 1fr"
        elif not self.library_visible and right_visible:
            main_panel.styles.grid_size_columns = 2
            main_panel.styles.grid_columns = "4fr 1fr"
        elif self.library_visible and not right_visible:
            main_panel.styles.grid_size_columns = 2
            main_panel.styles.grid_columns = "1fr 4fr"
        else:
            main_panel.styles.grid_size_columns = 1
            main_panel.styles.grid_columns = "1fr"

        main_panel.styles.grid_size_rows = 1

    def action_open_commands(self) -> None:
        """Show the command palette."""
        self.app.action_open_command_palette()

    def action_open_help(self) -> None:
        """Show the help palette."""
        self.app.action_open_help_palette()

    def action_handle_escape(self) -> None:
        """Handle Escape key press on player screen."""
        # First check if the app has an active palette
        if self.app.active_palette:
            self.app.active_palette.remove()
            self.app.active_palette = None
            return

        # Also look for any other palette
        try:
            # Use try-except instead of default parameter for compatibility
            search_palette = self.app.query_one("SearchPalette")
            search_palette.remove()
            return
        except Exception:
            # No palette found, which is fine
            pass

        # No need to handle other cases here - let the default handler work
