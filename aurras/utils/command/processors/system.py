"""
System processor for Aurras CLI.

This module handles system-related commands and operations such as
cache management, disk usage, and system information.
"""

import time
import sqlite3
import logging
import questionary
from typing import Dict, List, Tuple, Optional

from rich.console import Console

from ...path_manager import PathManager
from ...theme_helper import ThemeHelper, with_error_handling
from ...cache_cleanup import cleanup_all_caches
from ...console.renderer import ListDisplay, FeedbackMessage

logger = logging.getLogger(__name__)
console = Console()
path_manager = PathManager()


class SystemProcessor:
    """Handle system-related commands and operations."""

    def __init__(self):
        """Initialize the system processor."""
        pass

    @with_error_handling
    def show_cache_info(self) -> int:
        """
        Display information about cached data with theme-consistent styling.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        primary_color = ThemeHelper.get_theme_color("primary", "cyan")
        info_color = ThemeHelper.get_theme_color("info", "blue")
        dim_color = ThemeHelper.get_theme_color("dim", "dim")

        cache_header: List[Tuple[str, str, str, str]] = []

        try:
            with console.status(
                f"[{info_color}]Analyzing cache information...", spinner="dots"
            ):
                if path_manager.cache_db.exists():
                    with sqlite3.connect(path_manager.cache_db) as conn:
                        cursor = conn.cursor()

                        # Count search entries
                        cursor.execute("SELECT COUNT(*) FROM cache")
                        search_count = cursor.fetchone()[0]

                        # Count lyrics entries
                        cursor.execute("SELECT COUNT(*) FROM lyrics")
                        lyrics_count = cursor.fetchone()[0]

                        # Get oldest entry
                        cursor.execute("SELECT MIN(fetch_time) FROM cache")
                        oldest_search = cursor.fetchone()[0]
                        cursor.execute("SELECT MIN(fetch_time) FROM lyrics")
                        oldest_lyrics = cursor.fetchone()[0]

                        oldest = min(
                            oldest_search or float("inf"), oldest_lyrics or float("inf")
                        )
                        if oldest and oldest != float("inf"):
                            oldest_date = time.strftime(
                                "%Y-%m-%d", time.localtime(oldest)
                            )
                        else:
                            oldest_date = "N/A"

                        size = path_manager.cache_db.stat().st_size
                        size_str = f"{size / 1024:.1f} KB"

                        cache_header = [
                            ("Cache Type", "Entries", "Size", "Oldest Entry"),
                            (
                                "Total",
                                str(search_count + lyrics_count),
                                size_str,
                                oldest_date,
                            ),
                            ("Searches", str(search_count), "-", oldest_date),
                            ("Lyrics", str(lyrics_count), "-", oldest_date),
                        ]

                        table = ListDisplay(
                            items=cache_header,
                            title="Cache Information",
                            description=f"Use 'cleanup_cache' to clean old cache entries",
                            show_indices=False,
                            use_table=True,
                            style_key="primary",
                        )
                else:
                    cache_header = [
                        ("Cache Type", "Entries", "Size", "Oldest Entry"),
                        ("Searches", "0", "0 KB", "N/A"),
                        ("Lyrics", "0", "0 KB", "N/A"),
                    ]

                    table = ListDisplay(
                        items=cache_header,
                        title="Cache Information",
                        description="Cache database not found or empty",
                        show_indices=False,
                        use_table=True,
                        style_key="primary",
                    )

            console.print(table.render())

            console.print(
                f"[{dim_color}]Tip: Use [bold {primary_color}]cleanup_cache[/bold {primary_color}] to clear old cache entries[/{dim_color}]"
            )
            return 0

        except Exception as e:
            error_color = ThemeHelper.get_theme_color("error", "red")
            console.print(
                f"[bold {error_color}]Error getting cache info:[/bold {error_color}] {str(e)}"
            )
            logger.error(f"Error in show_cache_info: {str(e)}", exc_info=True)
            return 1

    @with_error_handling
    def cleanup_cache(self, days: Optional[int] = 30) -> int:
        """
        Clean up old cached data with theme-consistent styling.

        Args:
            days: Number of days of cache to keep (older entries are deleted)

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        # Get theme colors for consistent styling
        info_color = ThemeHelper.get_theme_color("info", "cyan")
        success_color = ThemeHelper.get_theme_color("success", "green")

        # Convert string input to int if needed
        days_to_keep = days
        if isinstance(days, str) and days.isdigit():
            days_to_keep = int(days)

        # If no days provided or invalid, ask the user
        if days_to_keep is None or days_to_keep < 0:
            days_input = questionary.text(
                "Keep cache newer than how many days?", default="30"
            ).ask()

            try:
                days_to_keep = int(days_input)
            except (ValueError, TypeError):
                error_color = ThemeHelper.get_theme_color("error", "red")
                console.print(
                    f"[{error_color}]Invalid input. Using default of 30 days.[/{error_color}]"
                )
                days_to_keep = 30

        try:
            with console.status(
                f"[bold {info_color}]Cleaning up cache older than {days_to_keep} days...",
                spinner="dots",
            ):
                results = cleanup_all_caches(days_to_keep)

            # Show results with theme-consistent styling
            if sum(results.values()) > 0:
                feedback = FeedbackMessage(
                    message=f"Cache cleanup complete",
                    action=f"Removed entries older than {days_to_keep} days",
                    style="success",
                )
                console.print(feedback.render())

                # List details with theme-consistent styling
                for cache_type, count in results.items():
                    if count > 0:
                        console.print(
                            f"  - {cache_type.title()}: [bold {success_color}]{count}[/] entries deleted"
                        )
            else:
                feedback = FeedbackMessage(
                    message="Cache is already clean!",
                    action=f"No entries older than {days_to_keep} days found",
                    style="info",
                )
                console.print(feedback.render())

            return 0
        except Exception as e:
            error_color = ThemeHelper.get_theme_color("error", "red")
            console.print(
                f"[bold {error_color}]Error cleaning cache:[/bold {error_color}] {str(e)}"
            )
            logger.error(f"Error in cleanup_cache: {str(e)}", exc_info=True)
            return 1


# Instantiate processor for direct import
processor = SystemProcessor()
