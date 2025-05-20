"""
Library processor for Aurras CLI.

This module handles library-related commands and operations such as
searching, indexing, and managing the media library.
"""

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.utils.decorators import with_error_handling

logger = get_logger("aurras.command.processors.library", log_to_console=False)


class LibraryProcessor:
    """Handle library-related commands and operations."""

    def __init__(self):
        """Initialize the library processor."""

    @with_error_handling
    def search(self, query: str, limit: int = 5) -> int:
        """
        Search for music across all sources.

        Args:
            query: Search query
            limit: Maximum number of results to show (default: 5)

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        if not query:
            console.print_error("Search query cannot be empty")
            return 1

        from aurras.services.youtube.search import YouTubeSearch

        try:
            # Create a status indicator while searching
            with console.status(
                console.style_text(f"Searching for '{query}'...", "info"),
                spinner="dots",
            ):
                youtube_search = YouTubeSearch()
                results = youtube_search.search(query, max_results=limit)

            if not results:
                console.print_warning(f"No results found for '{query}'")
                return 0

            # Create a table to display search results
            table = console.create_table(
                title=f"Search Results for '{query}'",
                caption=f"Found {len(results)} results",
            )

            table.add_column("#")
            table.add_column("Title")
            table.add_column("Artist")
            table.add_column("Duration")

            for i, result in enumerate(results, 1):
                table.add_row(
                    str(i),
                    result.get("title", "Unknown"),
                    result.get("artist", "Unknown"),
                    result.get("duration_str", "-"),
                )

            console.print(table)

            # Display a tip on how to play these results
            tip_panel = console.create_panel(
                f"Use 'play {query}' to play the first result",
                title="Tip",
                style="info",
            )
            console.print(tip_panel)
            return 0

        except Exception as e:
            logger.error(f"Error searching for '{query}': {e}")
            console.print_error(f"Error searching: {e}")
            return 1

    @with_error_handling
    def list_downloads(self) -> int:
        """
        List downloaded songs.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        try:
            downloads = self.downloader.list_downloads()

            if not downloads:
                console.print_info("No downloaded songs found")
                return 0

            # Create a table to display downloaded songs
            table = console.create_table(
                title="Downloaded Songs", caption=f"Total: {len(downloads)} song(s)"
            )

            table.add_column("Title")
            table.add_column("Artist")
            table.add_column("Size")
            table.add_column("Date")

            for download in downloads:
                # Format file size
                size = download["size"]
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"

                table.add_row(
                    download.get("title", "Unknown"),
                    download.get("artist", "Unknown"),
                    size_str,
                    download.get("date", "Unknown"),
                )

            console.print(table)
            return 0

        except Exception as e:
            logger.error(f"Error listing downloads: {e}")
            console.print_error(f"Error listing downloads: {e}")
            return 1
