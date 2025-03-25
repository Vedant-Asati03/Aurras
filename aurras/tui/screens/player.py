"""
Main player screen for Aurras TUI.
"""

import asyncio
import traceback
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Static, Label, ProgressBar, Button, Link
from textual.events import Click  # Add this import for click events
from textual import on
from textual.binding import Binding  # Add this import for key bindings

# Import the OptionList class for proper event handling
from textual.widgets import OptionList

# from ..widgets.player_controls import PlayerControls
from ..widgets.song_list import Queue, RecentlyPlayed
from ...player.online import ListenSongOnline  # Import for playing songs
from ...services.lyrics import LyricsFetcher  # Import for fetching lyrics
from ..widgets.search_palette import SearchPalette  # Add SearchPalette to the imports


class HomeScreen(Screen):
    """Main player screen with playback controls and queue."""

    # Add key bindings for the player screen
    BINDINGS = [
        Binding("1", "toggle_library_panel", "Toggle Library Panel", False),
        Binding("2", "toggle_queue_panel", "Toggle Queue", False),
        Binding("3", "toggle_recents_panel", "Toggle Recent Songs", False),
        Binding("4", "toggle_lyrics_size", "Toggle Lyrics Size", False),
        Binding("/", "open_search", "Search", id="binding"),  # Search mode
        Binding(">", "open_commands", "Commands", id="binding"),  # Command mode
        Binding("?", "open_help", "Help", id="binding"),  # Help mode
        Binding("escape", "handle_escape", "Close", id="binding"),
    ]

    def __init__(self):
        """Initialize the player screen."""
        super().__init__()
        self.current_song = None
        self.lyrics_fetcher = None
        self.lyrics_expanded = False
        self.library_visible = True
        self.queue_visible = True
        self.recents_visible = True

    def compose(self) -> ComposeResult:
        """Compose the player screen layout."""

        with Horizontal(id="main-container"):
            left_panel = Vertical(id="left-panel")
            left_panel.border_title = "¹library"
            with left_panel:
                playlist = VerticalScroll(id="playlist-container")
                playlist.border_title = "playlists"
                with playlist:
                    ...
                downloads = VerticalScroll(id="downloads-container")
                downloads.border_title = "downloads"
                with downloads:
                    ...

            player = Vertical(id="player-panel")
            player.border_title = "AURRAS"
            with player:
                # Song info
                song_info = Horizontal(id="song-info")
                song_info.border_title = "player"
                with song_info:
                    song_name = Container(id="song-name")
                    with song_name:
                        yield Label("Song Title", id="song-title")
                        yield Label("Artist - Album", id="song-details")

                    cover = Container(id="cover-container", classes="bordered")
                    # cover.border_title = "Cover"
                    with cover:
                        yield Label("Cover Image", id="cover-image")

                # Playback controls
                # yield PlayerControls(id="playback-controls")

                # Current lyrics preview with added class for initial size
                lyrics_preview = Container(
                    id="lyrics-preview", classes="bordered lyrics-normal"
                )
                lyrics_preview.border_title = "⁴lyrics"
                lyrics_preview.border_subtitle = (
                    "~vol 100"  # Changed brackets to parentheses
                )
                with lyrics_preview:
                    yield Static(
                        "No song playing...",
                        id="lyrics-text",
                    )
                    # yield Button("Show Full Lyrics", id="show-lyrics")
                # Progress bar
                with Horizontal(id="info-control-container"):
                    with Horizontal(id="progress-info"):
                        yield Label("03:45", id="time-total")
                        yield ProgressBar(
                            total=100, id="song-progress", show_percentage=False
                        )
                    with Horizontal(id="controls"):
                        yield Button(label="", id="previous", classes="control-button")
                        yield Button(label="", id="stop", classes="control-button")
                        yield Button(
                            label="", id="play-pause", classes="control-button"
                        )

            # Right panel (queue)
            # link = Link("v1.1.1", "https://github.com/vedant-asati03/aurras/")
            right_panel = Vertical(id="right-panel")
            right_panel.border_subtitle = "v1.1.1"
            with right_panel:
                yield Queue(id="song-queue")
                yield RecentlyPlayed(id="recently-played")

        f = Footer(show_command_palette=False)
        f.styles.color = "green"
        yield f
        # yield Footer(show_command_palette=False , id="app-footer")

    def on_mount(self) -> None:
        """Handle the screen mount event."""
        # Update progress bar periodically
        self.set_interval(0.5, self._update_progress)

        # Initialize progress bar value
        progress_bar = self.query_one("#song-progress", ProgressBar)
        progress_bar.value = 30

        # Setup update timers for queue and history
        self.set_interval(5, self._refresh_displays)

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
            queue = self.query_one("#song-queue", Queue)
            queue._refresh_queue()

            recents = self.query_one("#recently-played", RecentlyPlayed)
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

    def action_toggle_library_panel(self) -> None:
        """Toggle visibility of the library panel (left panel)."""
        main_panel = self.query_one("#main-container", Horizontal)
        left_panel = self.query_one("#left-panel", Vertical)

        self.library_visible = not self.library_visible

        if self.library_visible:
            main_panel.styles.grid_size_columns = 3
            main_panel.styles.grid_size_rows = 1
            main_panel.styles.grid_columns = "1fr 3fr 1fr"
            left_panel.styles.display = "block"
        else:
            left_panel.styles.display = "none"

        # Update the overall layout after this change
        self._update_main_layout()

    def action_toggle_queue_panel(self) -> None:
        """Toggle visibility of the queue panel."""
        right_panel = self.query_one("#right-panel", Vertical)
        queue_panel = self.query_one("#song-queue", Queue)
        recents_panel = self.query_one("#recently-played", RecentlyPlayed)

        self.queue_visible = not self.queue_visible

        if self.queue_visible:
            queue_panel.styles.display = "block"
            queue_panel.styles.height = "60%"
            recents_panel.styles.height = "40%"
        else:
            queue_panel.styles.display = "none"
            recents_panel.styles.height = "100%"

        # Check if both queue and recents are hidden
        if not self.queue_visible and not self.recents_visible:
            right_panel.styles.display = "none"
        else:
            right_panel.styles.display = "block"

        # Update the overall layout after this change
        self._update_main_layout()

    def action_toggle_recents_panel(self) -> None:
        """Toggle visibility of the recently played panel."""
        recents_panel = self.query_one("#recently-played", RecentlyPlayed)
        queue_panel = self.query_one("#song-queue", Queue)
        right_panel = self.query_one("#right-panel", Vertical)

        self.recents_visible = not self.recents_visible

        if self.recents_visible:
            recents_panel.styles.display = "block"
            queue_panel.styles.height = "60%"
            recents_panel.styles.height = "40%"
        else:
            recents_panel.styles.display = "none"
            queue_panel.styles.height = "100%"

        # Check if both queue and recents are hidden
        if not self.queue_visible and not self.recents_visible:
            right_panel.styles.display = "none"
        else:
            right_panel.styles.display = "block"

        # Update the overall layout after this change
        self._update_main_layout()

    def _update_main_layout(self) -> None:
        """Update the main layout based on which panels are visible."""
        main_panel = self.query_one("#main-container", Horizontal)

        if self.library_visible and (self.queue_visible or self.recents_visible):
            main_panel.styles.grid_size_columns = 3
            main_panel.styles.grid_columns = "1fr 3fr 1fr"

        elif not self.library_visible and (self.queue_visible or self.recents_visible):
            main_panel.styles.grid_size_columns = 2
            main_panel.styles.grid_columns = "4fr 1fr"

        elif self.library_visible and not (self.queue_visible or self.recents_visible):
            main_panel.styles.grid_size_columns = 2
            main_panel.styles.grid_columns = "1fr 4fr"

        else:
            main_panel.styles.grid_size_columns = 1
            main_panel.styles.grid_columns = "1fr"

        main_panel.styles.grid_size_rows = 1

    def action_open_search(self) -> None:
        """Show the search palette as a floating overlay."""
        self.app.action_open_search_palette()

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
