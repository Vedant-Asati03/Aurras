"""
System processor for Aurras CLI.

This module handles system-related commands and operations such as
cache management, disk usage, and system information.
"""

import time
import sqlite3
from typing import Optional

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.utils.path_manager import _path_manager
from aurras.utils.console.renderer import ListDisplay
from aurras.utils.decorators import with_error_handling

logger = get_logger("aurras.command.processors.system", log_to_console=False)


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
        if _path_manager.cache_db.exists():
            with sqlite3.connect(_path_manager.cache_db) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM cache) AS search_count,
                    (SELECT COUNT(*) FROM lyrics) AS lyrics_count,
                    (SELECT MIN(fetch_time) FROM cache) AS oldest_search,
                    (SELECT MIN(fetch_time) FROM lyrics) AS oldest_lyrics
                """)

                search_count, lyrics_count, oldest_search, oldest_lyrics = (
                    cursor.fetchone()
                )

                oldest = min(
                    oldest_search or float("inf"), oldest_lyrics or float("inf")
                )
                if oldest and oldest != float("inf"):
                    oldest_date = time.strftime("%Y-%m-%d", time.localtime(oldest))
                else:
                    oldest_date = "N/A"

                size = _path_manager.cache_db.stat().st_size
                size_str = f"{size / 1024:.1f} KB"

                info = ListDisplay(
                    items=[
                        ("Searches", str(search_count)),
                        ("Lyrics", str(lyrics_count)),
                        ("Size", size_str),
                        ("Oldest Entry", oldest_date),
                    ],
                    title="Cache Information",
                    description="Use 'cleanup_cache' to clean old cache entries",
                    highlight_style="primary",
                )

                console.print(info.render())
                return 0

    @with_error_handling
    def cleanup_cache(self, days: Optional[int] = 30) -> int:
        """
        Clean up old cached data with theme-consistent styling.

        Args:
            days: Number of days of cache to keep (older entries are deleted)

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        # Convert string input to int if needed
        # days_to_keep = days
        # if isinstance(days, str) and days.isdigit():
        #     days_to_keep = int(days)

        # # If no days provided or invalid, ask the user using the themed prompt
        # if days_to_keep is None or days_to_keep < 0:
        #     days_input = console.prompt(
        #         "Keep cache newer than how many days?",
        #         style_key="primary",
        #         default="30",
        #     )

        #     try:
        #         days_to_keep = int(days_input)
        #     except (ValueError, TypeError):
        #         console.print_error("Invalid input. Using default of 30 days.")
        #         days_to_keep = 30

        # try:
        #     # Create a themed status display while cleaning
        #     with console.status(
        #         console.style_text(
        #             f"Cleaning up cache older than {days_to_keep} days...",
        #             "info",
        #             bold=True,
        #         ),
        #         spinner="dots",
        #     ):
        #         results = cleanup_all_caches(days_to_keep)

        #     # Show results with theme-consistent styling
        #     if sum(results.values()) > 0:
        #         # Create a panel for the success message
        #         feedback_panel = console.create_panel(
        #             f"Removed entries older than {days_to_keep} days",
        #             title="Cache Cleanup Complete",
        #             style="success",
        #             border_style="success",
        #         )
        #         console.print(feedback_panel)

        #         # Create a table for detailed results
        #         results_table = console.create_table()
        #         results_table.add_column("Cache Type")
        #         results_table.add_column("Entries Deleted")

        #         for cache_type, count in results.items():
        #             if count > 0:
        #                 results_table.add_row(cache_type.title(), str(count))

        #         console.print(results_table)
        #     else:
        #         feedback = FeedbackMessage(
        #             message="Cache is already clean!",
        #             action=f"No entries older than {days_to_keep} days found",
        #             style="info",
        #         )
        #         console.print(feedback.render())

        #     return 0
        # except Exception as e:
        #     console.print_error(f"Error cleaning cache: {str(e)}")
        #     logger.error(f"Error in cleanup_cache: {str(e)}", exc_info=True)
        #     return 1

    def toggle_lyrics(self):
        """Toggle the display of lyrics."""
        from aurras.utils.command.processors.settings import SettingsProcessor

        settings_processor = SettingsProcessor()

        # Use confirmation prompt
        if console.confirm(
            "Do you want to toggle lyrics display?", style_key="primary"
        ):
            settings_processor.toggle_setting(setting_name="display-lyrics")
            console.print_success("Lyrics display setting toggled successfully")
        else:
            console.print_info("Operation cancelled")
