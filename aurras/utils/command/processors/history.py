"""
History processor for Aurras CLI.

This module handles playback history-related commands and operations such as
viewing, clearing, and managing the playback history.
"""

import time
from typing import List, Tuple

from aurras.utils.console import console
from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.utils.console.renderer import ListDisplay
from aurras.utils.decorators import with_error_handling
from aurras.core.player.history import RecentlyPlayedManager

logger = get_logger("aurras.command.processors.history")


def format_timestamp_from_settings(timestamp: float) -> str:
    """
    Format a timestamp based on user settings for date and time format.

    Args:
        timestamp: Unix timestamp to format

    Returns:
        Formatted timestamp string based on user preferences
    """
    date_format = SETTINGS.appearance_settings.date_format
    time_format = SETTINGS.appearance_settings.time_format

    formatted_date_pattern = {
        "yyyy-mm-dd": "%Y-%m-%d",
        "dd-mm-yyyy": "%d-%m-%Y",
        "mm-dd-yyyy": "%m-%d-%Y",
    }

    formatted_time_pattern = {
        "12h": "%I:%M %p",
        "24h": "%H:%M",
    }

    full_format = f"{formatted_date_pattern.get(date_format, '%Y-%m-%d')} {formatted_time_pattern.get(time_format, '%H:%M')}"

    return time.strftime(full_format, time.localtime(timestamp))


class HistoryProcessor:
    """Handle playback history-related commands and operations."""

    def __init__(self):
        """Initialize the history processor."""
        self.history_manager = RecentlyPlayedManager()

    @with_error_handling
    def show_history(self, limit: str = 10) -> int:
        """
        Show recent playback history.

        Args:
            limit: Maximum number of history items to show

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        with logger.operation_context(operation="history_display"):
            limit = int(limit)
            recent_songs = self.history_manager.get_recent_songs(limit=limit)
            history_count = self.history_manager.get_history_count()

            logger.info(
                "Retrieved playback history",
                extra={
                    "operation": "history_display",
                    "requested_limit": limit,
                    "returned_count": len(recent_songs),
                    "total_history_count": history_count,
                },
            )

            if not recent_songs:
                console.print_error("No playback history found")
                return 0

            formatted_items: List[Tuple[str, str]] = []

            for song in recent_songs:
                timestamp = format_timestamp_from_settings(song["played_at"])

                source = song["source"]
                if source == "search":
                    source_display = " search"
                elif source == "playlist":
                    source_display = "󰲹 playlist"
                elif source == "offline":
                    source_display = " offline"
                else:
                    source_display = source

                play_count = song.get("play_count", 1)
                count_display = f" (played {play_count}×)" if play_count > 1 else ""

                description = f"{timestamp} · {source_display}{count_display}"
                formatted_items.append((song["song_name"], description))

            title = f"Your Listening history (Showing {len(recent_songs)} of {history_count})"

            description = (
                f"Use [bold {console.success}]'--history-limit NUMBER'[/] "
                f"[{console.dim}]to show more or fewer songs[/]"
            )

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
    def clear_history(self) -> int:
        """
        Clear the playback history.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        with logger.operation_context(operation="history_clear"):
            logger.info(
                "Clearing playback history",
                extra={"operation": "history_clear"},
            )

            self.history_manager.clear_history()

            logger.info(
                "Playback history cleared successfully",
                extra={"operation": "history_clear"},
            )

            return 0

    @with_error_handling
    def play_previous_song(self, index: int = 0) -> int:
        """
        Replay a track from playback history.

        Args:
            index: Index of the history item to replay (0 = most recent)

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        with logger.operation_context(operation="history_replay"):
            prev_song = self.history_manager.get_previous_song()

            if prev_song:
                logger.info(
                    "Playing previous song from history",
                    extra={
                        "operation": "history_replay",
                        "song_name": prev_song,
                        "index": index,
                    },
                )

                play_message = (
                    f"[bold {console.success}]Playing previous song:[/bold {console.success}] "
                    f"[{console.primary}]{prev_song}[/{console.primary}]"
                )
                console.print(play_message)

                from aurras.utils.command.processors import processor

                processor.player_processor.play_song(
                    song_name=prev_song,
                    show_lyrics=True,
                )

            else:
                logger.warning(
                    "No previous songs found in history",
                    extra={
                        "operation": "history_replay",
                        "index": index,
                    },
                )

                console.print_warning(
                    "No previous songs found in your listening history. "
                    "Try playing a few songs first to build your history."
                )
            return 0
