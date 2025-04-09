"""
Progress bar rendering for the MPV player.

This module provides functionality for creating and updating the
player progress bar with gradient effects.
"""

import logging
from rich.progress import TextColumn, BarColumn, Progress
from ...utils.gradient_utils import get_gradient_style

logger = logging.getLogger(__name__)


def create_progress_bar(elapsed: float, duration: float) -> Progress:
    """
    Create a progress bar for song playback with gradient effect.

    Args:
        elapsed: Current playback position in seconds
        duration: Song duration in seconds

    Returns:
        Rich Progress object with styled progress bar
    """
    # Get theme colors for progress
    style = get_gradient_style()
    progress_colors = style.get("progress", ["cyan", "green"])

    # Use the first color for the bar and the second for completed sections
    bar_color = progress_colors[0]
    complete_color = progress_colors[-1]

    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=30, style=bar_color, complete_style=complete_color),
        TextColumn("[bold cyan]{task.fields[time]} / {task.fields[duration]}"),
    )

    # Calculate progress percentage
    percent_complete = min(
        100, max(0, (elapsed / duration) * 100 if duration > 0 else 0)
    )

    return progress


def add_playback_task(
    progress: Progress, playback_state: str, elapsed: float, duration: float
) -> None:
    """
    Add a playback task to the progress bar.

    Args:
        progress: Progress bar instance
        playback_state: Current playback state (PLAYING/PAUSED)
        elapsed: Current playback position in seconds
        duration: Song duration in seconds
    """
    # Get playback status text
    play_status = "[red] PAUSED[/red]" if playback_state == "PAUSED" else " PLAYING"

    # Calculate percentage
    percent_complete = min(
        100, max(0, (elapsed / duration) * 100 if duration > 0 else 0)
    )

    # Add task to progress
    progress.add_task(
        f"[bold]{play_status}[/]",
        total=100,
        completed=percent_complete,
        time=format_time(elapsed),
        duration=format_time(duration),
    )


def format_time(seconds: float) -> str:
    """
    Format time in seconds to MM:SS format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string in MM:SS format
    """
    if seconds is None or seconds < 0:
        return "0:00"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"
