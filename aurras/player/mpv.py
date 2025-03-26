"""MPV player with enhanced UI and functionality."""

import time
import threading
import locale
from typing import Dict, Any
from rich.console import Console, Group
from rich.panel import Panel
from rich.live import Live
from rich.progress import TextColumn, BarColumn, Progress
from rich.text import Text
from rich.box import ROUNDED

from . import python_mpv as mpv

try:
    from ..services.lyrics import LyricsFetcher, LYRICS_AVAILABLE
except ImportError:
    LyricsFetcher = None
    LYRICS_AVAILABLE = False


class MPVError(Exception):
    """Custom exception for MPV-related errors."""

    pass


class MPVPlayer(mpv.MPV):
    """Enhanced MPV player with better UI and extended functionality."""

    def __init__(
        self,
        ytdl: bool = True,
        ytdl_format: str = "bestaudio",
        volume: int = 100,
        loglevel: str = "warn",
    ):
        """Initialize the MPV player with customized settings."""

        locale.setlocale(locale.LC_NUMERIC, "C")

        super().__init__(
            ytdl=ytdl,
            ytdl_format=ytdl_format,
            input_default_bindings=True,
            input_vo_keyboard=True,
            osc=True,
            terminal=True,
            video=False,
            aid="auto",
            ao="pulse,alsa,",  # Try PulseAudio first, then ALSA, then auto
            cache=True,
            cache_secs=10,
            demuxer_readahead_secs=5,
            gapless_audio=True,  # Enable gapless audio playback
            af="aresample=precision=28",
            audio_resample_filter_size=16,
            audio_resample_phase_shift=10,
            hr_seek="yes",
        )

        self.console = Console()
        self.lyrics_fetcher = None
        self._is_playing = False
        self._stop_requested = False
        self._progress_thread = None
        self._progress_instance = None
        self._elapsed_time = 0

        self.volume = volume

        self.observe_property("pause", self._on_pause_change)
        self.observe_property("duration", self._on_duration_change)
        self.observe_property("metadata", self._on_metadata_change)

        self._metadata = {
            "title": "Unknown",
            "artist": "Unknown",
            "album": "Unknown",
            "duration": 0,
        }

        try:
            self._set_property("msg-level", f"all={loglevel}")
        except Exception:
            pass

        self._setup_key_bindings()

        @self.property_observer("time-pos")
        def _get_elapsed_time(_name, value):
            self._elapsed_time = value

    def _setup_key_bindings(self):
        """Set up key bindings using different available methods."""
        try:
            self.keybind("q", self._handle_quit_event)
            self.keybind("SPACE", self._handle_pause_event)
            self.keybind("RIGHT", self._handle_seek_forward_event)
            self.keybind("LEFT", self._handle_seek_backward_event)
            self.keybind("UP", self._handle_volume_up_event)
            self.keybind("DOWN", self._handle_volume_down_event)
        except Exception as e:
            self.console.print(f"[dim]Warning: Primary keybinding failed: {e}[/]")

    def _handle_quit_event(self):
        """Handle quit key event."""
        self._stop_requested = True
        self.console.print("[yellow]Quitting on user request (q)[/]")
        self.quit()

    def _handle_pause_event(self):
        """Handle pause key event."""
        self.toggle_pause()

    def _handle_seek_forward_event(self):
        """Handle right arrow key event."""
        self.seek_relative(10)

    def _handle_seek_backward_event(self):
        """Handle left arrow key event."""
        self.seek_relative(-10)

    def _handle_volume_up_event(self):
        """Handle up arrow key event."""
        self.set_volume(self.volume + 5)

    def _handle_volume_down_event(self):
        """Handle down arrow key event."""
        self.set_volume(self.volume - 5)

    def player(
        self,
        path_url: str,
        current_song: str,
        show_lyrics: bool = True,
        display_progress: bool = True,
    ) -> int:
        """Play media with enhanced UI and functionality."""
        self._stop_requested = False
        self._is_playing = True
        result_code = 0

        try:
            self.play(path_url)

            if show_lyrics and LYRICS_AVAILABLE and LyricsFetcher:
                self._display_lyrics(current_song)

            self._start_display(current_song)

            try:
                self.wait_for_playback()
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Playback interrupted by user[/]")
            except Exception as e:
                self.console.print(f"[bold red]Playback error: {e}[/]")

            return result_code

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Playback interrupted by user[/]")
            return 0
        except Exception as e:
            self.console.print(f"[bold red]Playback Error:[/] {str(e)}")
            return 1
        finally:
            self._stop_display()

            if self.lyrics_fetcher:
                try:
                    self.lyrics_fetcher.stop_lyrics_monitor()
                except Exception:
                    pass

            try:
                self.stop()
                self._is_playing = False
                self._stop_requested = True
            except Exception:
                pass

    def _start_display(self, song_name: str) -> None:
        """Start a beautiful live display showing playback info and controls."""
        self._display_thread = threading.Thread(
            target=self._run_display, args=(song_name,), daemon=True
        )
        self._display_thread.start()

    def _stop_display(self) -> None:
        """Stop the display cleanly."""
        self._stop_requested = True
        if (
            hasattr(self, "_display_thread")
            and self._display_thread
            and self._display_thread.is_alive()
        ):
            try:
                self._display_thread.join(timeout=1.0)
            except Exception:
                pass

    def _run_display(self, song_name: str) -> None:
        """Run the live display showing song information and playback status."""
        try:
            controls_text = (
                "[white][bold cyan]Space[/]:Pause · "
                "[bold cyan]Q[/]:Quit · "
                "[bold cyan]←→[/]:Seek · "
                "[bold cyan]↑↓[/]:Volume[/]"
            )

            with Live(refresh_per_second=4, console=self.console) as live:
                while not self._stop_requested and self._is_playing:
                    elapsed = (
                        self._elapsed_time if self._elapsed_time is not None else 0
                    )
                    duration = self.duration if self.duration is not None else 0
                    progress_percent = (elapsed / duration) * 100 if duration > 0 else 0

                    artist = self._metadata.get("artist", "Unknown")
                    album = self._metadata.get("album", "Unknown")
                    # title = self._metadata.get("title", song_name)

                    info_text = (
                        f"[bold green]Now Playing:[/] [bold yellow]{song_name}[/]"
                    )
                    if artist != "Unknown" and artist.strip():
                        info_text += f"\n[bold magenta]Artist:[/] [yellow]{artist}[/]"
                    if album != "Unknown" and album.strip():
                        info_text += (
                            f" [dim]·[/] [bold magenta]Album:[/] [yellow]{album}[/]"
                        )

                    progress = Progress(
                        TextColumn("[bold blue]{task.description}"),
                        BarColumn(bar_width=40, style="cyan", complete_style="green"),
                        TextColumn(
                            "[bold cyan]{task.fields[time]} / {task.fields[duration]}"
                        ),
                    )

                    play_status = "▐▐ PAUSED" if self.pause else "▶ PLAYING"
                    progress.add_task(
                        f"[bold]{play_status}[/]",
                        total=100,
                        completed=progress_percent,
                        time=self._format_time(elapsed),
                        duration=self._format_time(duration),
                    )

                    status_text = f"[dim]Status: {'Paused' if self.pause else 'Playing'} · Volume: {self.volume}%[/]"

                    content = Group(
                        info_text,
                        progress,
                        status_text,
                        controls_text,
                    )

                    panel = Panel(
                        content,
                        title="♫ Aurras Music Player ♫",
                        border_style="cyan",
                        box=ROUNDED,
                        padding=(0, 1),
                    )

                    live.update(panel)
                    time.sleep(0.5)

        except Exception as e:
            self.console.print(f"[bold red]Display error: {str(e)}[/]")
            import traceback

            self.console.print(traceback.format_exc())

    def _display_lyrics(self, current_song: str) -> None:
        """Show lyrics for the current song."""
        try:
            self.console.print("[dim]Fetching lyrics...[/]")
            self.lyrics_fetcher = LyricsFetcher(current_song)
            self.lyrics_fetcher.display_lyrics()
            self.lyrics_fetcher.start_lyrics_monitor()
        except Exception as e:
            self.console.print(f"[yellow]Could not display lyrics:[/] {str(e)}")

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to MM:SS format."""
        if seconds is None or seconds < 0:
            return "0:00"

        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"

    def _get_metadata_display(self) -> str:
        """Get a formatted string with current metadata."""
        artist = self._metadata.get("artist", "Unknown")
        album = self._metadata.get("album", "Unknown")

        if artist != "Unknown" and album != "Unknown":
            return f"{artist} - {album}"
        elif artist != "Unknown":
            return f"{artist}"
        elif album != "Unknown":
            return f"{album}"
        else:
            return ""

    def _on_pause_change(self, name: str, value: bool) -> None:
        """Handle pause state changes."""
        # Remove console prints that add extra lines to the output
        pass

    def _on_duration_change(self, name: str, value: float) -> None:
        """Handle duration property changes."""
        if value and value > 0:
            self._metadata["duration"] = value

    def _on_metadata_change(self, name: str, value: Dict[str, Any]) -> None:
        """Handle metadata changes."""
        if value:
            # Remove debugging metadata print
            # Update our metadata store with new values
            if "title" in value:
                self._metadata["title"] = value["title"]
            if "artist" in value:
                self._metadata["artist"] = value["artist"]
            if "album" in value:
                self._metadata["album"] = value["album"]

            # For some files, metadata might be in different keys
            # Check icy-title, a common streaming metadata key
            if "icy-title" in value and "title" not in value:
                # Try to extract artist and title from icy-title
                icy_title = value["icy-title"]
                if " - " in icy_title:
                    artist, title = icy_title.split(" - ", 1)
                    self._metadata["artist"] = artist
                    self._metadata["title"] = title
                else:
                    self._metadata["title"] = icy_title

    def _toggle_pause(self) -> None:
        """Toggle pause state."""
        self.toggle_pause()

    def _handle_quit(self) -> None:
        """Handle quit key press."""
        self._stop_requested = True
        self.quit()

    # Enhanced API for other modules to use
    def get_playback_info(self) -> Dict[str, Any]:
        """Get current playback information."""
        return {
            "is_playing": not self.pause,
            "position": self.time_pos or 0,
            "duration": self.duration or 0,
            "volume": self.volume,
            "metadata": self._metadata.copy(),
        }

    def toggle_pause(self) -> bool:
        """Toggle between play and pause states."""
        try:
            self.pause = not self.pause
            return self.pause
        except Exception:
            return False

    def seek_relative(self, seconds: float) -> None:
        """Seek forward or backward relative to current position."""
        try:
            current_pos = self.time_pos or 0
            new_pos = max(0, current_pos + seconds)
            self.seek(new_pos, reference="absolute")
            self.console.print(f"[dim]Seek to {self._format_time(new_pos)}[/]")
        except Exception as e:
            self.console.print(f"[yellow]Seek failed:[/] {str(e)}")

    def set_volume(self, volume: int) -> None:
        """Set the player volume."""
        try:
            self.volume = max(0, min(130, volume))  # Clamp to 0-130
            self.console.print(f"[dim]Volume: {self.volume}%[/]")
        except Exception as e:
            self.console.print(f"[yellow]Volume change failed:[/] {str(e)}")
