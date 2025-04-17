"""
History command processor for Aurras CLI.

This module handles playback history operations.
"""

import time
import logging
from typing import List, Tuple

from .player import PlayerProcessor
from ....player.history import RecentlyPlayedManager
from ...console.manager import get_console
from ...console.renderer import (
    ListDisplay,
)
from ...theme_helper import ThemeHelper, with_error_handling

logger = logging.getLogger(__name__)
console = get_console()


class HistoryProcessor:
    """Handle history-related commands and operations."""

    def __init__(self):
        """Initialize the history processor."""
        self.history_manager = RecentlyPlayedManager()

    @with_error_handling
    def display_history(self, limit=30):
        """Display recently played songs up to the specified limit."""
        # Get theme colors
        theme_styles = ThemeHelper.get_theme_colors()
        info_color = theme_styles.get("info", "blue")

        with console.status(
            f"[bold {info_color}]Loading your listening history...", spinner="dots"
        ):
            # Get history data
            recent_songs = self.history_manager.get_recent_songs(limit=limit)
            history_count = self.history_manager.get_history_count()

        if not recent_songs:
            warning_color = theme_styles.get("warning", "yellow")
            console.print(
                f"[italic {warning_color}]No song history found.[/italic {warning_color}]"
            )
            return 0

        # Format the history data for ListDisplay
        formatted_items: List[Tuple[str, str]] = []

        for song in recent_songs:
            # Format the timestamp
            timestamp = time.strftime(
                "%Y-%m-%d %H:%M", time.localtime(song["played_at"])
            )

            # Format source with emoji based on type
            source = song["source"]
            if source == "search":
                source_display = " search"
            elif source == "playlist":
                source_display = "󰲹 playlist"
            elif source == "offline":
                source_display = " offline"
            else:
                source_display = source

            # Get play count, defaulting to 1 for older entries
            play_count = song.get("play_count", 1)
            count_display = f" (played {play_count}×)" if play_count > 1 else ""

            # Add to formatted items
            description = f"{timestamp} · {source_display}{count_display}"
            formatted_items.append((song["song_name"], description))

        # Create title with theme-consistent styling
        title = (
            f"Your Listening history (Showing {len(recent_songs)} of {history_count})"
        )

        # Create description with tips
        success_color = theme_styles.get("success", "green")
        dim_color = theme_styles.get("dim", "dim")
        description = f"Use [bold {success_color}]'--history-limit NUMBER'[/bold {success_color}] [{dim_color}]to show more or fewer songs[/{dim_color}]"

        # Create and display the ListDisplay component
        history_list = ListDisplay(
            items=formatted_items,
            title=title,
            description=description,
            show_indices=True,
            use_table=True,
            style_key="primary",
            max_height=limit,
        )

        console.print(history_list.render())
        return 0

    @with_error_handling
    def clear_history(self):
        """Clear the song play history."""
        self.history_manager.clear_history()
        return 0

    @with_error_handling
    def play_previous_song(self):
        """Play the previous song from history."""
        theme_styles = ThemeHelper.get_theme_colors()
        success_color = theme_styles.get("success", "green")
        warning_color = theme_styles.get("warning", "yellow")
        primary_color = theme_styles.get("primary", "cyan")
        dim_color = theme_styles.get("dim", "dim")

        with console.status(
            f"[bold {success_color}]Finding previous song in history",
            spinner="aesthetic",
        ):
            prev_song = self.history_manager.get_previous_song()

        if prev_song:
            console.print(
                f"[bold {success_color}]Playing previous song:[/bold {success_color}] [{primary_color}]{prev_song}[/{primary_color}]"
            )
            PlayerProcessor().play_song(
                song_name=prev_song,
                show_lyrics=True,
            )

        else:
            console.print(
                f"[{warning_color}]No previous songs found in your listening history.[/{warning_color}]"
            )
            console.print(
                f"[{dim_color}]Try playing a few songs first to build your history.[/{dim_color}]"
            )
        return 0


# Instantiate processor for direct import
processor = HistoryProcessor()
