"""
Lyrics Module

This module provides functionality for fetching, displaying, and translating song lyrics.
"""

import threading
import sqlite3
import json
from rich.console import Console
from rich.panel import Panel
from rich.box import ROUNDED

# Use try-except to handle missing dependencies gracefully
try:
    import keyboard

    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("Warning: keyboard module not installed. Some features will be limited.")

try:
    from googletrans import Translator

    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    print("Warning: googletrans not installed. Translation will not be available.")

try:
    from lyrics_extractor import SongLyrics

    LYRICS_AVAILABLE = True
except ImportError:
    LYRICS_AVAILABLE = False
    print("Warning: lyrics_extractor not installed. Lyrics will not be available.")
    print("To enable lyrics, install with: pip install lyrics-extractor")

from ..utils.terminal import clear_screen
from ..core.settings import LoadDefaultSettings
from ..utils.path_manager import PathManager

_path_manager = PathManager()


class LyricsCache:
    """Class for managing the lyrics cache."""

    def __init__(self):
        """Initialize the lyrics cache database."""
        self.cache_db = _path_manager.lyrics_cache_db
        self._initialize_db()
        self.console = Console()

    def _initialize_db(self):
        """Create the lyrics cache table if it doesn't exist."""
        with sqlite3.connect(self.cache_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lyrics_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    song_name TEXT UNIQUE,
                    lyrics TEXT,
                    fetched_at INTEGER
                )
            """)
            conn.commit()

    def get_lyrics(self, song_name):
        """
        Get lyrics for a song from the cache.

        Args:
            song_name: Name of the song

        Returns:
            The lyrics if found, None otherwise
        """
        try:
            with sqlite3.connect(self.cache_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT lyrics FROM lyrics_cache WHERE song_name = ?", (song_name,)
                )
                result = cursor.fetchone()
                if result:
                    return result[0]
        except Exception as e:
            self.console.print(f"[yellow]Error reading lyrics from cache: {e}[/yellow]")
        return None

    def save_lyrics(self, song_name, lyrics):
        """
        Save lyrics to the cache.

        Args:
            song_name: Name of the song
            lyrics: Lyrics to save
        """
        try:
            import time

            with sqlite3.connect(self.cache_db) as conn:
                cursor = conn.cursor()
                timestamp = int(time.time())
                cursor.execute(
                    "INSERT OR REPLACE INTO lyrics_cache (song_name, lyrics, fetched_at) VALUES (?, ?, ?)",
                    (song_name, lyrics, timestamp),
                )
                conn.commit()
        except Exception as e:
            self.console.print(f"[yellow]Error saving lyrics to cache: {e}[/yellow]")


class LyricsManager:
    """Base class for lyrics functionality."""

    def __init__(self):
        """Initialize the LyricsManager class."""
        self.console = Console()
        self.api_key = None
        self.lyrics_cache = LyricsCache()

        # Only try to initialize SongLyrics if it's available
        if LYRICS_AVAILABLE:
            try:
                self.api_key = SongLyrics(
                    "AIzaSyAcZ6KgA7pCIa_uf8-bYdWR85vx6-dWqDg", "aa2313d6c88d1bf22"
                )
            except Exception as e:
                self.console.print(
                    f"[yellow]Failed to initialize lyrics API: {e}[/yellow]"
                )

        self.settings = LoadDefaultSettings().load_default_settings()
        self.lyrics_thread = None
        self.stop_event = threading.Event()

    def should_show_lyrics(self):
        """Check if lyrics should be shown based on settings and available modules."""
        # Don't show lyrics if the required module is missing
        if not LYRICS_AVAILABLE:
            return False

        return self.settings.get("show-lyrics", "yes").lower() == "yes"


class LyricsFetcher(LyricsManager):
    """Class for fetching and managing song lyrics."""

    def __init__(self, song_name):
        """Initialize with the song name."""
        super().__init__()
        self.song_name = song_name
        self.lyrics = None
        self.fetch_lyrics()

    def fetch_lyrics(self):
        """Fetch lyrics for the song from the cache or API."""
        if not self.should_show_lyrics():
            return

        # Try to get lyrics from cache first
        cached_lyrics = self.lyrics_cache.get_lyrics(self.song_name)

        if cached_lyrics:
            self.console.print("[cyan]Found lyrics in cache[/cyan]")
            self.lyrics = cached_lyrics
            return

        # If not in cache and API key is available, fetch from API
        if not self.api_key:
            return

        try:
            with self.console.status(
                f"[cyan]Fetching lyrics for {self.song_name}...[/cyan]"
            ):
                result = self.api_key.get_lyrics(self.song_name)
                self.lyrics = result["lyrics"]

                # Save to cache for future use
                self.lyrics_cache.save_lyrics(self.song_name, self.lyrics)

        except Exception as e:
            self.console.print(f"[yellow]Could not fetch lyrics: {str(e)}[/yellow]")
            self.lyrics = None

    def display_lyrics(self):
        """Display the fetched lyrics in a formatted panel."""
        if not self.lyrics or not self.should_show_lyrics():
            return

        # Create a nice panel with the lyrics
        panel = Panel(
            self.lyrics,
            title=f"🎵 Lyrics: {self.song_name} 🎵",
            border_style="cyan",
            box=ROUNDED,
            padding=(1, 2),
            width=min(100, self.console.width - 4),
        )

        self.console.print("\n")
        self.console.print(panel)

        if TRANSLATOR_AVAILABLE and KEYBOARD_AVAILABLE:
            self.console.print(
                "[dim]Press 't' during playback to translate lyrics[/dim]"
            )

    def start_lyrics_monitor(self):
        """Start a background thread to monitor for the 't' key to translate lyrics."""
        if (
            not self.lyrics
            or not self.should_show_lyrics()
            or not KEYBOARD_AVAILABLE
            or not TRANSLATOR_AVAILABLE
        ):
            return

        self.stop_event.clear()
        self.lyrics_thread = threading.Thread(
            target=self._monitor_translation_key, daemon=True
        )
        self.lyrics_thread.start()

    def stop_lyrics_monitor(self):
        """Stop the lyrics monitor thread."""
        if self.lyrics_thread and self.lyrics_thread.is_alive():
            self.stop_event.set()
            self.lyrics_thread.join(timeout=1)

    def _monitor_translation_key(self):
        """Monitor for the 't' key to translate lyrics."""
        if not TRANSLATOR_AVAILABLE or not KEYBOARD_AVAILABLE:
            return

        try:
            translator = Translator(
                service_urls=["translate.google.com", "translate.google.co.kr"]
            )
        except Exception as e:
            self.console.print(f"[yellow]Failed to initialize translator: {e}[/yellow]")
            return

        translated = False
        original_lyrics = self.lyrics

        while not self.stop_event.is_set():
            try:
                if keyboard.is_pressed("t"):
                    clear_screen()

                    if not translated:
                        # Translate the lyrics
                        with self.console.status("[cyan]Translating lyrics...[/cyan]"):
                            try:
                                translated_text = translator.translate(
                                    self.lyrics, dest="en"
                                ).text
                                self.lyrics = translated_text
                                translated = True
                            except Exception as e:
                                self.console.print(
                                    f"[yellow]Translation failed: {e}[/yellow]"
                                )
                                continue
                    else:
                        # Revert to original lyrics
                        self.lyrics = original_lyrics
                        translated = False

                    # Display the updated lyrics
                    self.display_lyrics()

                    # Prevent multiple presses
                    self.console.print(
                        "[dim]Translation toggled. Press 'q' to return to playback.[/dim]"
                    )
                    self.stop_event.wait(1)  # Small delay to avoid rapid toggling
            except Exception:
                # Ignore keyboard detection errors
                pass

            self.stop_event.wait(0.1)  # Small delay to reduce CPU usage
