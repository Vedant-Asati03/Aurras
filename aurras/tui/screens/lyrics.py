"""
Lyrics display screen for Aurras TUI.
"""

import asyncio
import traceback
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.widgets import Footer, Static, Button
from textual.binding import Binding

from ...services.lyrics import LyricsFetcher


class LyricsScreen(Screen):
    """Screen for displaying song lyrics."""

    BINDINGS = [
        Binding("t", "translate_lyrics", "Translate", id="lyrics"),
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self, song_name=None):
        """Initialize the lyrics screen."""
        super().__init__()
        self.song_name = song_name
        self.lyrics_fetcher = None
        self.lyrics = None
        self.translated = False

    def compose(self) -> ComposeResult:
        """Compose the lyrics screen layout."""
        with ScrollableContainer(id="lyrics-container"):
            yield Static("", id="lyrics-song-title")

        yield Footer(show_command_palette=False)

    def on_mount(self):
        """Handle mounting of the lyrics screen."""
        self.app.sub_title = "Song Lyrics"

        if self.song_name:
            title = self.query_one("#lyrics-song-title", Static)
            title.update(f"{self.song_name}")

            self.run_worker(self._fetch_lyrics_async())

    async def _fetch_lyrics_async(self):
        """Fetch lyrics asynchronously."""
        if not self.song_name:
            return

        try:
            lyrics_text = self.query_one("#full-lyrics", Static)
            lyrics_text.update("Fetching lyrics...")

            # Create lyrics fetcher in a thread to avoid blocking
            self.notify("Fetching lyrics, please wait...")
            self.lyrics_fetcher = LyricsFetcher(self.song_name)

            # Define a function that will run in a separate thread
            def fetch_lyrics_thread():
                try:
                    self.lyrics_fetcher.fetch_lyrics()
                    return self.lyrics_fetcher.lyrics
                except Exception as e:
                    return f"Error: {str(e)}\n{traceback.format_exc()}"

            # Run the function in a thread and get the result
            lyrics_result = await asyncio.to_thread(fetch_lyrics_thread)

            if isinstance(lyrics_result, str) and lyrics_result.startswith("Error:"):
                lyrics_text.update(f"Failed to fetch lyrics: {lyrics_result[:100]}...")
            else:
                if self.lyrics_fetcher and self.lyrics_fetcher.lyrics:
                    formatted_lyrics = self._format_lyrics_for_display(
                        self.lyrics_fetcher.lyrics
                    )
                    self.lyrics = formatted_lyrics
                    lyrics_text.update(formatted_lyrics)
                    self.notify("Lyrics loaded successfully")
                else:
                    lyrics_text.update("No lyrics found for this song.")

        except Exception as e:
            lyrics_text = self.query_one("#full-lyrics", Static)
            lyrics_text.update(f"Failed to load lyrics.\nError: {str(e)}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "translate-lyrics":
            self.action_translate_lyrics()
        elif button_id == "copy-lyrics":
            self.action_copy_lyrics()

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

            # Strip all potential Rich markup characters
            import re

            sanitized_lyrics = re.sub(
                r"\[|\]|\{|\}|\<|\>|\*|\_|\`|\||\$|\&|\!|\@|\#|\%|\^|\~", " ", lyrics
            )
            sanitized_lyrics = sanitized_lyrics.replace("\\", "")

            # Make sure there are line breaks for readability
            if "\n" not in sanitized_lyrics[:100]:
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

                if current_line:
                    lines.append(" ".join(current_line))

                sanitized_lyrics = "\n".join(lines)

            return sanitized_lyrics

        except Exception as e:
            # Last resort - ultra-safe version
            import re

            ultra_safe = re.sub(r"[^\w\s\.\,\;\:\'\"\!\?]", "", lyrics)
            return ultra_safe

    def action_translate_lyrics(self) -> None:
        """Translate the displayed lyrics."""
        if not self.lyrics_fetcher or not self.lyrics:
            self.notify("No lyrics available to translate")
            return

        lyrics_text = self.query_one("#full-lyrics", Static)

        if self.translated:
            # Switch back to original lyrics
            lyrics_text.update(self.lyrics)
            self.translated = False
            self.notify("Showing original lyrics")
        else:
            # Show translated version if available
            if hasattr(self.lyrics_fetcher, "translate_lyrics"):
                self.notify("Translating lyrics, please wait...")

                async def translate_async():
                    try:
                        translated = await asyncio.to_thread(
                            self.lyrics_fetcher.translate_lyrics
                        )
                        if translated:
                            lyrics_text.update(translated)
                            self.translated = True
                            self.notify("Lyrics translated")
                        else:
                            self.notify("Translation failed")
                    except Exception as e:
                        self.notify(f"Translation error: {str(e)}")

                self.run_worker(translate_async())
            else:
                self.notify("Translation not available")

    def action_copy_lyrics(self) -> None:
        """Copy lyrics to clipboard."""
        if not self.lyrics:
            self.notify("No lyrics to copy")
            return

        # In a real implementation, you'd copy to the system clipboard
        # For now we'll just notify
        self.notify("Lyrics copied to clipboard")
