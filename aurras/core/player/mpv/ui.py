"""
UI rendering module for the MPV player.

This module provides enhanced UI components for the player interface
with consistent styling, animations, and theme integration.
It uses the component-based architecture from the console renderer system.
"""

from typing import Optional, Dict, Any, List, Tuple

from rich.console import Group
from rich.columns import Columns

from aurras.core.player.mpv.state import FeedbackType, PlaybackState, UserFeedback
from aurras.utils.console import console, apply_gradient_to_text
from aurras.utils.console.renderer import (
    UIComponent,
    ProgressIndicator,
    FeedbackMessage,
    KeybindingHelp,
    UIRenderer,
)


class SongInfoComponent(UIComponent):
    """Component to display song information with rich formatting."""

    def __init__(
        self,
        song: str,
        artist: str,
        album: str,
        source: str = "",
        playlist_position: int = 0,
        playlist_count: int = 0,
    ):
        """
        Initialize song information component.

        Args:
            song: Song name
            artist: Artist name
            album: Album name
            source: Song source indicator (e.g., From History)
            playlist_position: Current position in playlist
            playlist_count: Total songs in playlis
        """
        self.song = song
        self.artist = artist
        self.album = album
        self.source = source
        self.playlist_position = playlist_position
        self.playlist_count = playlist_count

    def render(self) -> str:
        """Render song information with gradient styling."""
        info_text = ""

        if self.song:
            song_text = apply_gradient_to_text(
                self.song, console.title_gradient, bold=True
            )

            info_text = console.style_text(
                text=f"Now Playing: {song_text}",
                style_key="accent",
                text_style="bold",
            )

        if self.source:
            info_text += f" {self.source}"

        if self.artist and self.artist != "Unknown" and self.artist.strip():
            album_text = apply_gradient_to_text(self.artist, console.artist_gradient)

            artist_label_text = console.style_text(
                text="Artist:",
                style_key="accent",
                text_style="bold",
            )
            info_text += f"\n{artist_label_text} {album_text}"

        if self.album and self.album != "Unknown" and self.album.strip():
            album_text = apply_gradient_to_text(self.album, console.artist_gradient)

            artist_label_text = console.style_text(
                text="Album:",
                style_key="accent",
                text_style="bold",
            )
            info_text += f" [dim]·[/] {artist_label_text} {album_text}"

        if self.playlist_count > 0:
            position_info = console.style_text(
                text=f"Song {self.playlist_position + 1} of {self.playlist_count}",
                style_key="dim",
            )
            info_text += f"\n{position_info}"

        return info_text


class PlaybackProgressBar(UIComponent):
    """Enhanced progress bar for media playback."""

    def __init__(
        self,
        elapsed: float,
        duration: float,
        playback_state: PlaybackState,
        width: int = 30,
    ):
        """
        Initialize playback progress bar.

        Args:
            elapsed: Current playback position in seconds
            duration: Song duration in seconds
            playback_state: Current playback state
            width: Bar width in characters
        """
        self.elapsed = max(0, elapsed)
        self.duration = max(0.1, duration)  # Avoid division by zero
        self.playback_state = playback_state
        self.width = width

    def render(self) -> Any:
        """Render the playback progress bar."""

        indicator = ProgressIndicator(
            total=self.duration,
            completed=self.elapsed,
            description="" if self.playback_state == PlaybackState.PAUSED else "",
            unit="s",
            bar_width=self.width,
        )

        return indicator.render()


class StatusDisplay(UIComponent):
    """Component to display player status information."""

    def __init__(
        self,
        playback_state: PlaybackState,
        volume: int,
    ):
        """
        Initialize status display.

        Args:
            playback_state: Current playback state enum
            volume: Current volume level
        """
        self.playback_state = playback_state
        self.volume = volume

    def render(self) -> str:
        """Render the status text."""
        theme_info = f" · Theme: {console.theme_obj.name}" if console.theme_obj else ""

        status_text = f"Volume: {self.volume}%{theme_info}"

        return console.style_text(
            text=apply_gradient_to_text(status_text, console.status_gradient),
            style_key="dim",
        )


class QueueDisplay(UIComponent):
    """Component to display upcoming songs in the queue."""

    def __init__(
        self,
        upcoming_songs: List[str],
        current_position: int,
        max_songs: int = 3,
    ):
        """
        Initialize queue display component.

        Args:
            upcoming_songs: List of all song names in the queue
            current_position: Current position in the queue
            max_songs: Maximum number of upcoming songs to show
        """
        self.all_songs = upcoming_songs
        self.current_position = current_position
        self.max_songs = max_songs

    def render(self) -> Optional[str]:
        """Render upcoming songs in the queue with styled formatting."""
        if not self.all_songs or self.current_position >= len(self.all_songs) - 1:
            return None

        # Get upcoming songs
        upcoming = self.all_songs[self.current_position + 1 :]
        if not upcoming:
            return None

        # Limit to max_songs or 2
        upcoming = upcoming[: min(self.max_songs, 2)]

        # Format the queue display with song numbers
        queue_text = f"Upcoming: {', '.join(upcoming)}"

        return console.style_text(
            text=apply_gradient_to_text(queue_text, console.status_gradient),
            style_key="dim",
        )


class UserFeedbackDisplay(UIComponent):
    """Component to display user feedback notifications."""

    def __init__(self, feedback: Optional[UserFeedback] = None):
        """
        Initialize user feedback component.

        Args:
            feedback: UserFeedback object with action information
        """
        self.feedback = feedback

    def render(self) -> Optional[str]:
        """Render user feedback with theme-appropriate styling."""
        if not self.feedback:
            return None

        style_key = "feedback"
        if self.feedback.feedback_type == FeedbackType.ERROR:
            style_key = "error"
        elif self.feedback.feedback_type == FeedbackType.SYSTEM:
            style_key = "system"

        timeout = self.feedback.timeout

        if self.feedback.feedback_type == FeedbackType.SYSTEM:
            timeout = (
                self.feedback.timeout if hasattr(self.feedback, "timeout") else 3.0
            )
        elif self.feedback.feedback_type == FeedbackType.ERROR:
            timeout = (
                self.feedback.timeout if hasattr(self.feedback, "timeout") else 8.0
            )

        feedback_message = FeedbackMessage(
            message=self.feedback.description,
            action=self.feedback.action,
            style=style_key,
            timeout=timeout,
            created_at=self.feedback.timestamp
            if hasattr(self.feedback, "timestamp")
            else None,
        )

        # Don't display if the message has expired
        if feedback_message.is_expired():
            return None

        return feedback_message.render()


class LyricsDisplay(UIComponent):
    """Component for displaying time-synced lyrics."""

    def __init__(self, lyrics: List[Tuple[str, str]]):
        super().__init__()
        self.lyrics = lyrics

    def render(self):
        return self.lyrics


class PlayerControls(UIComponent):
    """Component to display available player controls."""

    def __init__(self, detailed: bool = False):
        """
        Initialize player controls display.

        Args:
            detailed: Whether to show detailed controls
        """
        self.detailed = detailed

    def render(self) -> Any:
        """Render the keyboard controls help."""
        # _, active_theme_styles = ThemeHelper.retrieve_theme_gradients_and_styles()

        keybindings = {
            "󱁐": "Pause",
            "q": "Quit",
            "b": "Prev",
            "n": "Next",
            "←→": "Seek",
            "↑↓": "Volume",
        }

        if self.detailed:
            keybindings.update(
                {
                    "l": "Lyrics",
                    "t": "Theme",
                    "s": "Search",
                    "p": "Playlist",
                    "r": "Repeat",
                    "?": "Help",
                }
            )

        return KeybindingHelp(
            keybindings,
            columns=3 if self.detailed else 2,
            key_style="accent",
            value_style="text_muted",
        ).render()


class PlayerLayout:
    """
    Manager class for the player UI layout and rendering.
    Uses component-based architecture for a flexible, themed UI.
    """

    def __init__(self):
        """
        Initialize the player UI layout manager.

        Args:
            console: Optional rich console instance
        """
        self.renderer = UIRenderer()
        self.live = None
        self._running = False

        # UI state
        self.show_lyrics = False
        self.show_history = False
        self.detailed_controls = False

    def create_player_ui(self, player_state: Dict[str, Any]) -> None:
        """
        Create and register all UI components based on player state.

        Args:
            player_state: Dictionary containing player state info
        """
        song = player_state.get("song", "Unknown")
        artist = player_state.get("artist", "Unknown")
        album = player_state.get("album", "Unknown")
        elapsed = player_state.get("elapsed", 0)
        duration = player_state.get("duration", 0)
        playback_state = player_state.get("playback_state", PlaybackState.STOPPED)
        volume = player_state.get("volume", 100)
        playlist_position = player_state.get("playlist_position", 0)
        playlist_count = player_state.get("playlist_count", 0)
        user_feedback = player_state.get("feedback", None)
        lyrics_content = player_state.get("lyrics_lines", [])
        song_list = player_state.get("song_names", [])

        self.renderer.components.clear()

        # Create song info component
        song_info = SongInfoComponent(
            song,
            artist,
            album,
            source="",
            playlist_position=playlist_position,
            playlist_count=playlist_count,
        )
        self.renderer.add_component("song_info", song_info)

        # Create progress bar component
        progress = PlaybackProgressBar(elapsed, duration, playback_state)
        self.renderer.add_component("progress", progress)

        # Create status display
        status = StatusDisplay(playback_state, volume)
        self.renderer.add_component("status", status)

        # Add queue display if songs are in queue
        if song_list and len(song_list) > 1 and playlist_position < len(song_list) - 1:
            queue = QueueDisplay(song_list, playlist_position)
            self.renderer.add_component("queue", queue)

        # Add user feedback if available
        if user_feedback:
            feedback = UserFeedbackDisplay(user_feedback)
            self.renderer.add_component("feedback", feedback)

        # Add lyrics if enabled
        if self.show_lyrics and lyrics_content:
            lyrics = LyricsDisplay(lyrics_content)
            self.renderer.add_component("lyrics", lyrics)

        # Add controls
        controls = PlayerControls(detailed=self.detailed_controls)
        self.renderer.add_component("controls", controls)

        self.renderer._layout_func = self._create_multi_panel_layout

    def _create_multi_panel_layout(self) -> Any:
        """
        Create a multi-panel layout with main content, lyrics and playlist.

        Returns:
            Rich renderable with appropriate column layout
        """
        left_renderable: List[Any] = []
        right_renderable: List[Any] = []

        for name, component in self.renderer.components.items():
            rendered = component.render()

            if rendered is None:
                continue

            if name == "lyrics":
                right_renderable.append(rendered)
            else:
                left_renderable.append(rendered)

        left_group = Group(*left_renderable) if left_renderable else ""

        if right_renderable and self.show_lyrics:
            right_renderable = (
                Group(*right_renderable)
                if len(right_renderable) > 1
                else right_renderable[0]
            )

            return Columns([left_group, right_renderable], width=50, expand=True)

        return left_group

    def toggle_lyrics(self) -> None:
        """Toggle visibility of lyrics display."""
        self.show_lyrics = not self.show_lyrics

    def toggle_history(self) -> None:
        """Toggle visibility of play history."""
        self.show_history = not self.show_history

    def toggle_detailed_controls(self) -> None:
        """Toggle between simple and detailed control display."""
        self.detailed_controls = not self.detailed_controls

    def start_live_ui(self, refresh_per_second: float = 4.0) -> None:
        """
        Start live updating UI.

        Args:
            refresh_per_second: UI refresh rate
        """
        self.renderer.start_live_display(refresh_per_second=refresh_per_second)
        self._running = True

    def stop_live_ui(self) -> None:
        """Stop the live UI updates."""
        self.renderer.stop_live_display()
        self._running = False

    def update(self, player_state: Dict[str, Any]) -> None:
        """
        Update the UI with current player state.

        Args:
            player_state: Dictionary with current player state
        """
        self.create_player_ui(player_state)
        if self._running:
            self.renderer.refresh()
