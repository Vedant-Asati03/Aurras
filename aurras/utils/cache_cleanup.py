"""
Cache Cleanup Module

This module provides functions for cleaning up cached data that may be outdated.
"""

import sqlite3
import time
from pathlib import Path
from rich.console import Console

from ..utils.path_manager import PathManager

_path_manager = PathManager()
console = Console()


def _cleanup_lyrics_cache(days_old=30):
    """
    Delete lyrics from the unified cache database that are older than the specified number of days.

    Args:
        days_old: Number of days after which cache entries should be deleted

    Returns:
        int: Number of entries deleted
    """
    try:
        cache_db_path = _path_manager.cache_db
        if not Path(cache_db_path).exists():
            return 0

        with sqlite3.connect(cache_db_path) as conn:
            cursor = conn.cursor()

            # Calculate the timestamp for entries older than days_old
            cutoff_time = int(time.time()) - (days_old * 24 * 60 * 60)

            # Get count before deletion
            cursor.execute(
                "SELECT COUNT(*) FROM lyrics WHERE fetch_time < ?", (cutoff_time,)
            )
            count = cursor.fetchone()[0]

            # Delete old entries
            cursor.execute("DELETE FROM lyrics WHERE fetch_time < ?", (cutoff_time,))
            conn.commit()

            return count
    except Exception as e:
        console.print(f"[yellow]Error cleaning lyrics cache: {e}[/yellow]")
        return 0


def _cleanup_search_cache(days_old=30):
    """
    Delete old search cache entries from the unified cache database.

    Args:
        days_old: Number of days after which cache entries should be deleted

    Returns:
        int: Number of entries deleted
    """
    try:
        cache_db_path = _path_manager.cache_db
        if not Path(cache_db_path).exists():
            return 0

        with sqlite3.connect(cache_db_path) as conn:
            cursor = conn.cursor()

            # Calculate the timestamp for entries older than days_old
            cutoff_time = int(time.time()) - (days_old * 24 * 60 * 60)

            # Get count before deletion
            cursor.execute(
                "SELECT COUNT(*) FROM cache WHERE fetch_time < ?", (cutoff_time,)
            )
            count = cursor.fetchone()[0]

            # Delete old entries
            cursor.execute("DELETE FROM cache WHERE fetch_time < ?", (cutoff_time,))
            conn.commit()

            return count
    except Exception as e:
        console.print(f"[yellow]Error cleaning search cache: {e}[/yellow]")
        return 0


def cleanup_all_caches(days_old=30):
    """
    Clean up all cache databases to remove old entries.

    Args:
        days_old: Number of days after which cache entries should be deleted

    Returns:
        dict: Count of entries deleted from each cache
    """
    results = {}

    # Cleanup lyrics cache in the unified database
    lyrics_deleted = _cleanup_lyrics_cache(days_old)
    results["lyrics"] = lyrics_deleted

    # Cleanup search cache in the unified database
    search_deleted = _cleanup_search_cache(days_old)
    results["searches"] = search_deleted

    # Add other cache cleanups here as needed

    return results
