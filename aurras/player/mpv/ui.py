"""
UI rendering module for the MPV player.

This module provides enhanced UI components for the player interface
with consistent styling, animations, and theme integration.
It uses the component-based architecture from the console renderer system.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple

from rich.box import HEAVY, ROUNDED
from rich.panel import Panel
from rich.console import Group, Console

from ...utils.console.manager import get_console
from ...utils.console.renderer import (
    UIComponent,
    Header,
    ProgressIndicator,
    FeedbackMessage,
    KeybindingHelp,
    UIRenderer,
    get_current_theme_instance,
    get_theme_styles,
    get_theme_gradients,
)
from ...themes import get_theme, get_current_theme
from ...themes.adapters import theme_to_rich_theme, get_gradient_styles

from .state import FeedbackType, PlaybackState, UserFeedback

logger = logging.getLogger(__name__)

# Get the current theme for consistent styling
current_theme_name = get_current_theme()
theme = get_theme(current_theme_name)


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
        # Get theme styles and gradients using the proper theme system method
        theme_obj = get_current_theme_instance()
        theme_styles = get_theme_styles(theme_obj)
        theme_gradients = get_theme_gradients(theme_obj)

        # Initialize display text
        info_text = ""

        # Format song name with title gradient
        if self.song:
            # Apply gradient to song title
            if "title" in theme_gradients:
                title_gradient = theme_gradients.get("title")
                song_text = self._apply_gradient_to_text(
                    self.song, title_gradient, bold=True
                )
            else:
                # Fallback to primary color if no gradient available
                primary_color = self._get_theme_color(theme_styles, "primary", "cyan")
                song_text = f"[bold {primary_color}]{self.song}[/bold {primary_color}]"

            # Use the header style for the "Now Playing" text
            header_color = self._get_theme_color(theme_styles, "header", "cyan")
            info_text = f"[bold {header_color}]Now Playing:[/] {song_text}"

        # Add source if available
        if self.source:
            info_text += f" {self.source}"

        # Add artist if available with artist gradient
        if self.artist and self.artist != "Unknown" and self.artist.strip():
            # Apply gradient to artist name
            if "artist" in theme_gradients:
                artist_gradient = theme_gradients.get("artist")
                album_text = self._apply_gradient_to_text(self.artist, artist_gradient)
            else:
                # Fallback to artist color from theme styles
                album_color = self._get_theme_color(theme_styles, "artist", "magenta")
                album_text = f"[{album_color}]{self.artist}[/{album_color}]"

            # Format artist label with consistent theme style
            album_label_color = self._get_theme_color(theme_styles, "artist", "magenta")
            artist_label_text = f"[bold {album_label_color}]Artist:[/]"
            info_text += f"\n{artist_label_text} {album_text}"

        # Add album if available with subtle styling
        if self.album and self.album != "Unknown" and self.album.strip():
            if "artist" in theme_gradients:
                artist_gradient = theme_gradients.get("artist")
                album_text = self._apply_gradient_to_text(self.album, artist_gradient)
            else:
                album_color = self._get_theme_color(theme_styles, "artist", "magenta")
                album_text = f"[{album_color}]{self.album}[/{album_color}]"

            album_label_color = self._get_theme_color(theme_styles, "artist", "magenta")
            artist_label_text = f"[bold {album_label_color}]Album:[/]"
            info_text += f" [dim]·[/] {artist_label_text} {album_text}"

        # Add position information if in playlist
        if self.playlist_count > 0:
            dim_color = self._get_theme_color(theme_styles, "dim", "dim")
            position_info = f"[{dim_color}]Song {self.playlist_position + 1} of {self.playlist_count}[/{dim_color}]"
            info_text += f"\n{position_info}"

        return info_text

    def _apply_gradient_to_text(
        self, text: str, gradient: list, bold: bool = False
    ) -> str:
        """
        Apply a gradient effect to text using theme colors.

        Args:
            text: The text to apply gradient to
            gradient: List of gradient colors
            bold: Whether to make the text bold

        Returns:
            Rich-formatted text with gradient applied
        """
        if not text or not gradient:
            return text

        # For very short text, just use the first color
        if len(text) <= 3:
            bold_prefix = "bold " if bold else ""
            return f"[{bold_prefix}{gradient[0]}]{text}[/{bold_prefix}{gradient[0]}]"

        # For longer text, create a gradient effect
        chars_per_color = max(1, len(text) // len(gradient))
        result = []

        for i, char in enumerate(text):
            color_index = min(i // chars_per_color, len(gradient) - 1)
            color = gradient[color_index]
            bold_prefix = "bold " if bold else ""
            result.append(f"[{bold_prefix}{color}]{char}[/{bold_prefix}{color}]")

        return "".join(result)

    def _get_theme_color(self, theme_styles, key: str, default: str) -> str:
        """
        Get a color from theme styles with fallback.

        Args:
            theme_styles: The theme styles dictionary
            key: The color key to look up
            default: Default color to use if key not found

        Returns:
            Color value as string
        """
        style = theme_styles.get(key)

        # Handle different return types
        if isinstance(style, str):
            return style
        elif hasattr(style, "color") and style.color:
            # It's a Style object with a color attribute
            return style.color.name if hasattr(style.color, "name") else default
        else:
            return default


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

        # Return the rendered progress bar
        return indicator.render()


class StatusDisplay(UIComponent):
    """Component to display player status information."""

    def __init__(
        self,
        playback_state: PlaybackState,
        volume: int,
        current_theme: Optional[str] = None,
    ):
        """
        Initialize status display.

        Args:
            playback_state: Current playback state enum
            volume: Current volume level
            current_theme: Current theme name
        """
        self.playback_state = playback_state
        self.volume = volume
        self.current_theme = current_theme

    def render(self) -> str:
        """Render the status text."""
        # Get theme styles and gradients for proper theming
        theme_obj = get_current_theme_instance()
        theme_styles = get_theme_styles(theme_obj)
        theme_gradients = get_theme_gradients(theme_obj)

        # Get the current theme name for display
        theme_name = (
            get_current_theme() if not self.current_theme else self.current_theme
        )

        # Convert PlaybackState enum to string
        if self.playback_state == PlaybackState.PAUSED:
            status = "Paused"
        elif self.playback_state == PlaybackState.PLAYING:
            status = "Playing"
        else:
            status = "Stopped"

        # Add theme info if available
        theme_info = f" · Theme: {theme_name}" if theme_name else ""

        # Build status text
        status_text = f"Status: {status} · Volume: {self.volume}%{theme_info}"

        # Apply gradient styling if available
        if "status" in theme_gradients and theme_gradients["status"]:
            # Apply subtle gradient with theme colors
            dim_color = self._get_theme_color(theme_styles, "dim", "dim")
            return f"[{dim_color}]{self._apply_gradient_to_text(status_text, theme_gradients['status'])}[/{dim_color}]"
        else:
            # Fallback to simple dim styling
            dim_color = self._get_theme_color(theme_styles, "dim", "dim")
            return f"[{dim_color}]{status_text}[/{dim_color}]"

    def _apply_gradient_to_text(
        self, text: str, gradient: list, bold: bool = False
    ) -> str:
        """Apply a gradient effect to text using theme colors."""
        if not text or not gradient:
            return text

        # For very short text, just use the first color
        if len(text) <= 3:
            bold_prefix = "bold " if bold else ""
            return f"[{bold_prefix}{gradient[0]}]{text}[/{bold_prefix}{gradient[0]}]"

        # For longer text, create a gradient effect
        chars_per_color = max(1, len(text) // len(gradient))
        result = []

        for i, char in enumerate(text):
            color_index = min(i // chars_per_color, len(gradient) - 1)
            color = gradient[color_index]
            bold_prefix = "bold " if bold else ""
            result.append(f"[{bold_prefix}{color}]{char}[/{bold_prefix}{color}]")

        return "".join(result)

    def _get_theme_color(self, theme_styles, key: str, default: str) -> str:
        """Get a color from theme styles with fallback."""
        style = theme_styles.get(key)

        if isinstance(style, str):
            return style
        elif hasattr(style, "color") and style.color:
            return style.color.name if hasattr(style.color, "name") else default
        else:
            return default


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

        # Choose style based on feedback type
        style_key = "feedback"
        if self.feedback.feedback_type == FeedbackType.ERROR:
            style_key = "error"
        elif self.feedback.feedback_type == FeedbackType.SYSTEM:
            style_key = "system"

        # Create the feedback message component
        feedback_message = FeedbackMessage(
            message=self.feedback.description,
            action=self.feedback.action,
            style=style_key,
        )

        return feedback_message.render()


class LyricsDisplay(UIComponent):
    """Component for displaying time-synced lyrics."""

    def __init__(
        self,
        lyrics_lines: List[Tuple[float, str]],
        current_time: float,
        visible_lines: int = 5,
        width: Optional[int] = None,
    ):
        """
        Initialize lyrics display.

        Args:
            lyrics_lines: List of (timestamp, text) tuples for each line
            current_time: Current playback time in seconds
            visible_lines: Number of lines to show at once
            width: Optional display width
        """
        self.lyrics_lines = lyrics_lines
        self.current_time = current_time
        self.visible_lines = visible_lines
        self.width = width

    def render(self) -> Panel:
        """Render current lyrics with highlight for current line."""
        # Get theme styles
        theme_name = get_current_theme()
        theme_obj = get_theme(theme_name)
        theme_styles = get_theme_styles(theme_obj)

        if not self.lyrics_lines:
            return Panel(
                "[dim italic]No lyrics available[/]",
                title="Lyrics",
                border_style=theme_styles.get("accent", "dim cyan"),
                width=self.width,
            )

        # Find the current line based on timestamp
        current_index = -1
        for i, (timestamp, _) in enumerate(self.lyrics_lines):
            if timestamp > self.current_time:
                break
            current_index = i

        # Handle case where we're before the first lyric
        if current_index < 0 and self.lyrics_lines:
            current_index = 0

        # Get visible range around current line
        half_visible = self.visible_lines // 2
        start_idx = max(0, current_index - half_visible)
        end_idx = min(len(self.lyrics_lines), start_idx + self.visible_lines)

        # Adjust start if we have room at the end
        if (
            end_idx < len(self.lyrics_lines)
            and end_idx - start_idx < self.visible_lines
        ):
            start_idx = max(0, end_idx - self.visible_lines)

        visible_lyrics = []

        # Get highlight colors from theme
        current_color = theme_styles.get("primary", "bold cyan")
        dim_color = theme_styles.get("dim", "dim cyan")

        # Format lyrics with highlight for current line
        for i in range(start_idx, end_idx):
            timestamp, text = self.lyrics_lines[i]

            # Format timestamp
            time_display = self._format_time_values(timestamp)

            # Style based on whether this is the current line
            if i == current_index:
                line = f"[{current_color}]{time_display}[/] [bold white]{text}[/]"
            else:
                line = f"[{dim_color}]{time_display}[/] [dim]{text}[/]"

            visible_lyrics.append(line)

        # Show pagination indicators if needed
        if start_idx > 0:
            visible_lyrics.insert(0, f"[{dim_color}]↑ more lyrics above[/]")
        if end_idx < len(self.lyrics_lines):
            visible_lyrics.append(f"[{dim_color}]↓ more lyrics below[/]")

        # Create lyrics panel
        return Panel(
            "\n".join(visible_lyrics),
            title="Lyrics",
            border_style=theme_styles.get("accent", "cyan"),
            width=self.width,
        )

    def _format_time_values(self, seconds: float) -> str:
        """
        Format time in seconds to MM:SS format.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        seconds = max(0, seconds)

        # Round to nearest second
        seconds = round(seconds)

        minutes = seconds // 60
        seconds %= 60

        return f"{minutes:02d}:{seconds:02d}"


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
        # Get theme styles
        theme_styles = get_theme_styles(theme)

        keybindings = {
            "󱁐": "Pause",
            "q": "Quit",
            "b": "Prev",
            "n": "Next",
            "←→": "Seek",
            "↑↓": "Volume",
        }

        # Add more controls in detailed mode
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

        # Render using our keybinding component with theme styles
        return KeybindingHelp(
            keybindings,
            columns=3 if self.detailed else 2,
            key_style=theme_styles.get("accent", "bold cyan"),
            value_style=theme_styles.get("text", "white"),
        ).render()


class PlayerLayout:
    """
    Manager class for the player UI layout and rendering.
    Uses component-based architecture for a flexible, themed UI.
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the player UI layout manager.

        Args:
            console: Optional rich console instance
        """
        self.console = console or get_console()
        self.renderer = UIRenderer(self.console)
        self.live = None
        self._running = False

        # UI state
        self.show_lyrics = False
        self.show_history = False
        self.detailed_controls = False

        # Get current theme for consistent styling
        self.current_theme_name = get_current_theme()
        self.theme = get_theme(self.current_theme_name)

    def create_player_ui(self, player_state: Dict[str, Any]) -> None:
        """
        Create and register all UI components based on player state.

        Args:
            player_state: Dictionary containing player state info
        """
        # Extract state info
        song = player_state.get("song", "Unknown")
        artist = player_state.get("artist", "Unknown")
        album = player_state.get("album", "Unknown")
        elapsed = player_state.get("elapsed", 0)
        duration = player_state.get("duration", 0)
        playback_state = player_state.get("playback_state", PlaybackState.STOPPED)
        volume = player_state.get("volume", 100)
        current_theme = player_state.get("theme", None)
        playlist_position = player_state.get("playlist_position", 0)
        playlist_count = player_state.get("playlist_count", 0)
        user_feedback = player_state.get("feedback", None)
        lyrics_lines = player_state.get("lyrics_lines", [])

        # Clear existing components
        self.renderer.components.clear()

        # Get theme styles for header
        theme_styles = get_theme_styles(self.theme)
        header_style = theme_styles.get("header", "cyan")

        # Create header with app name
        header = Header(
            "Aurras Music Player",
            "A rich terminal music experience",
            style="bold",
            box_style=ROUNDED,
        )
        self.renderer.add_component("header", header)

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
        status = StatusDisplay(playback_state, volume, current_theme)
        self.renderer.add_component("status", status)

        # Add user feedback if available
        if user_feedback:
            feedback = UserFeedbackDisplay(user_feedback)
            self.renderer.add_component("feedback", feedback)

        # Add lyrics if enabled
        if self.show_lyrics and lyrics_lines:
            lyrics = LyricsDisplay(lyrics_lines, elapsed)
            self.renderer.add_component("lyrics", lyrics)

        # Add controls
        controls = PlayerControls(detailed=self.detailed_controls)
        self.renderer.add_component("controls", controls)

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
        self.renderer.start_live_display(
            refresh_per_second=refresh_per_second, layout_func=self._create_layout
        )
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
        # Check if theme has changed and update if needed
        if "theme" in player_state and player_state["theme"] != self.current_theme_name:
            self.current_theme_name = player_state["theme"]
            self.theme = get_theme(self.current_theme_name)

        self.create_player_ui(player_state)
        if self._running:
            self.renderer.refresh()

    def _create_layout(self) -> Panel:
        """Create the panel layout for the UI."""
        # Bundle all components for the layout
        components = []
        for name, component in self.renderer.components.items():
            try:
                rendered = component.render()
                if rendered is not None:
                    components.append(rendered)
            except Exception as e:
                logger.error(f"Error rendering component {name}: {e}")
                components.append(f"[bold red]Error rendering {name}[/]")

        # Group all components for the final layout
        content = Group(*components)

        # Get border style and text styles from theme
        theme_styles = get_theme_styles(self.theme)
        border_style = theme_styles.get("primary", "cyan")
        title_style = theme_styles.get("header", "bold cyan")

        # Create the main panel with theme-based styling
        return Panel(
            content,
            title=f"[{title_style}]♫ Aurras Music Player ♫[/]",
            border_style=border_style,
            box=HEAVY,
            padding=(0, 2),
        )


# Legacy API compatibility functions
# These provide backward compatibility with code that uses the old function-based API


def format_song_info(song: str, artist: str, album: str, source: str) -> str:
    """
    Legacy compatibility function for song info formatting.

    Args:
        song: Song name
        artist: Artist name
        album: Album name
        source: Song source indicator

    Returns:
        Formatted song information
    """
    component = SongInfoComponent(song, artist, album, source)
    return component.render()


def get_status_text(
    playback_state: PlaybackState, volume: int, current_theme: str = None
) -> str:
    """
    Legacy compatibility function for status text.

    Args:
        playback_state: Current playback state enum
        volume: Current volume level
        current_theme: Current theme name

    Returns:
        Formatted status text
    """
    component = StatusDisplay(playback_state, volume, current_theme)
    return component.render()


def create_display_content(
    song: str,
    artist: str,
    album: str,
    elapsed: float,
    duration: float,
    playback_state: PlaybackState,
    volume: int,
    current_theme: str,
    playlist_position: int,
    playlist_count: int,
    user_feedback: UserFeedback = None,
    history_text: str = None,
    lyrics_section: str = "",
) -> Group:
    """
    Legacy compatibility function for creating display content.

    Creates all UI components and renders them as a group for compatibility.

    Args:
        song: Song name
        artist: Artist name
        album: Album name
        elapsed: Current playback position in seconds
        duration: Song duration in seconds
        playback_state: Current playback state
        volume: Current volume level
        current_theme: Current theme name
        playlist_position: Current playlist position
        playlist_count: Total playlist count
        user_feedback: Current user feedback if any
        history_text: History information text if available
        lyrics_section: Formatted lyrics content

    Returns:
        Group of rendered components
    """
    # Create components
    components = []

    # Song info
    song_info = SongInfoComponent(
        song, artist, album, "", playlist_position, playlist_count
    )
    components.append(song_info.render())

    # Progress bar
    progress = PlaybackProgressBar(elapsed, duration, playback_state)
    components.append(progress.render())

    # Status display
    status = StatusDisplay(playback_state, volume, current_theme)
    components.append(status.render())

    # Add history if available
    if history_text:
        components.append(history_text)

    # Add feedback if available
    if user_feedback:
        feedback = UserFeedbackDisplay(user_feedback)
        feedback_text = feedback.render()
        if feedback_text:
            components.append(feedback_text)

    # Add lyrics if provided
    if lyrics_section:
        components.append(lyrics_section)

    return Group(*components)


def get_user_feedback_text(feedback: UserFeedback) -> str:
    """
    Legacy compatibility function for formatting user feedback.

    Args:
        feedback: UserFeedback object with action information

    Returns:
        Formatted feedback text
    """
    if not feedback:
        return None

    component = UserFeedbackDisplay(feedback)
    return component.render()


def create_player_panel(content, controls_text) -> Panel:
    """
    Legacy compatibility function for creating the player panel.

    Args:
        content: The panel content
        controls_text: Text showing available keyboard controls

    Returns:
        Styled panel with content
    """
    # Get current theme for styling
    current_theme = get_current_theme()
    theme_obj = get_theme(current_theme)
    theme_styles = get_theme_styles(theme_obj)

    # Get the border style from theme
    border_style = theme_styles.get("primary", "cyan")

    return Panel(
        content,
        title="♫ Aurras Music Player ♫",
        border_style=border_style,
        box=HEAVY,
        padding=(0, 1),
        subtitle=controls_text,
        subtitle_align="right",
    )


def get_controls_text() -> str:
    """
    Legacy compatibility function for keyboard controls.

    Returns:
        Rich formatted text for keyboard controls
    """
    # Get theme styles using adapter
    theme_name = get_current_theme()
    theme_obj = get_theme(theme_name)
    theme_styles = get_theme_styles(theme_obj)

    controls = PlayerControls(detailed=False)
    return str(controls.render())
