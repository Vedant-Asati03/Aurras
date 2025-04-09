"""
UI rendering functions for the MPV player.

This module provides functions for rendering the player UI components
with consistent styling and theme integration.
"""

import time
import logging
from rich.box import HEAVY
from rich.panel import Panel
from rich.console import Group
from rich.live import Live

from ...utils.gradient_utils import (
    apply_gradient_to_text,
    create_subtle_gradient_text,
    get_gradient_style,
)
from .progress import create_progress_bar, add_playback_task, format_time
from .state import FeedbackType, PlaybackState, UserFeedback

logger = logging.getLogger(__name__)


def format_song_info(song: str, artist: str, album: str, source: str) -> str:
    """
    Format song information for display with subtle gradients.

    Args:
        song: Song name
        artist: Artist name
        album: Album name
        source: Song source indicator (e.g., From History)

    Returns:
        Formatted song information with theme-consistent gradients
    """
    # Get the gradient style for the current theme
    style = get_gradient_style()

    # Start with song name using title gradient
    info_text = f"[bold green]Now Playing:[/] {apply_gradient_to_text(song, 'title', bold=True)}{source}"

    # Add artist if available with artist gradient
    if artist != "Unknown" and artist.strip():
        artist_text = apply_gradient_to_text(artist, "artist")
        info_text += f"\n[bold magenta]Artist:[/] {artist_text}"

    # Add album if available
    if album != "Unknown" and album.strip():
        album_text = create_subtle_gradient_text(album, "artist")
        info_text += f" [dim]·[/] [bold magenta]Album:[/] {album_text}"

    return info_text


def get_status_text(
    playback_state: PlaybackState, volume: int, current_theme: str = None
) -> str:
    """
    Get the current player status text with subtle gradient effects.

    Args:
        playback_state: Current playback state enum
        volume: Current volume level
        current_theme: Current theme name

    Returns:
        Formatted status text
    """
    # Convert PlaybackState enum to string
    if playback_state == PlaybackState.PAUSED:
        status = "Paused"
    elif playback_state == PlaybackState.PLAYING:
        status = "Playing"
    else:
        status = "Stopped"

    # Add theme info if available
    theme_info = f" · Theme: {current_theme}" if current_theme else ""

    # Apply subtle gradient to the status text
    status_text = create_subtle_gradient_text(
        f"Status: {status} · Volume: {volume}%{theme_info}", "status"
    )
    return f"[dim]{status_text}[/dim]"


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
    Create the content for the player UI display.

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
        Rich Group containing the formatted display content
    """
    # Format source information
    source = ""  # This would be populated based on history vs. searched songs

    # Format song information with history
    info_text = format_song_info(song, artist, album, source)

    # Add position information
    position_info = f"[dim]Song {playlist_position + 1} of {playlist_count}[/dim]"
    info_text += f"\n{position_info}"

    # Create progress bar
    progress = create_progress_bar(elapsed, duration)
    add_playback_task(
        progress,
        "PAUSED" if playback_state == PlaybackState.PAUSED else "PLAYING",
        elapsed,
        duration,
    )

    # Get status text
    status_text = get_status_text(playback_state, volume, current_theme)

    # Get user feedback if available
    user_feedback_text = (
        get_user_feedback_text(user_feedback) if user_feedback else None
    )

    # Combine elements into a group
    elements = [info_text, progress, status_text]

    # Add history text if available
    if history_text:
        elements.append(history_text)

    # Add user feedback if available
    if user_feedback_text:
        elements.append(user_feedback_text)

    # Add lyrics if enabled
    if lyrics_section:
        elements.append(lyrics_section)

    return Group(*elements)


def get_user_feedback_text(feedback: UserFeedback) -> str:
    """
    Format user feedback with gradient styling.

    Args:
        feedback: UserFeedback object with action information

    Returns:
        Formatted feedback text with theme-appropriate styling
    """
    if not feedback:
        return None

    # Apply gradients based on the current theme and feedback type
    gradient_type = "feedback"
    if feedback.feedback_type == FeedbackType.ERROR:
        gradient_type = "error"
    elif feedback.feedback_type == FeedbackType.SYSTEM:
        gradient_type = "system"

    styled_action = apply_gradient_to_text(feedback.action, gradient_type, bold=True)
    styled_description = create_subtle_gradient_text(
        feedback.description, gradient_type
    )

    return f"\n► {styled_action}: {styled_description}"


def create_player_panel(content, controls_text) -> Panel:
    """
    Create a themed panel for the player display.

    Args:
        content: The panel content
        controls_text: Text showing available keyboard controls

    Returns:
        Rich Panel with styled border and formatting
    """
    return Panel(
        content,
        title="♫ Aurras Music Player ♫",
        border_style="cyan",
        box=HEAVY,
        padding=(0, 1),
        subtitle=controls_text,
        subtitle_align="right",
    )


def get_controls_text() -> str:
    """
    Get formatted text describing available keyboard controls.

    Returns:
        Rich formatted text for keyboard controls
    """
    return (
        "[white][bold cyan]󱁐[/] Pause · "
        "[bold cyan]q[/] Quit · "
        "[bold cyan]b[/] Prev · "
        "[bold cyan]n[/] Next · "
        "[bold cyan]←→[/] Seek · "
        "[bold cyan]↑↓[/] Volume · "
        "[bold cyan]l[/] Lyrics · "
        "[bold cyan]t[/] Theme[/]"
    )
