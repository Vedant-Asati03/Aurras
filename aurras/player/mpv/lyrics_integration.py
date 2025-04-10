"""
Lyrics integration for the MPV player.

This module provides functionality for fetching, formatting and displaying
lyrics in the MPV player interface with theme-consistent styling.
"""

import logging
from concurrent.futures import Future

from ..lyrics_handler import LyricsHandler
from ..memory import optimize_memory_usage
from ..cache import LRUCache
from ...themes.manager import get_theme, get_current_theme

from .state import LyricsStatus, LyricsState

logger = logging.getLogger(__name__)


@optimize_memory_usage()
def prefetch_lyrics(
    song: str,
    artist: str,
    album: str,
    duration: int,
    lyrics_handler: LyricsHandler,
    lyrics_cache: LRUCache,
    thread_pool,
    active_futures: set = None,
) -> Future:
    """
    Prefetch lyrics asynchronously with optimized memory usage.

    Args:
        song: Song name
        artist: Artist name
        album: Album name
        duration: Song duration in seconds
        lyrics_handler: Lyrics handler instance
        lyrics_cache: Lyrics cache instance
        thread_pool: ThreadPoolExecutor instance for async fetching
        active_futures: Set to track active futures for cleanup

    Returns:
        Future for the async operation
    """

    # Define the fetch function with weak references to avoid memory leaks
    def fetch_lyrics():
        try:
            # First check memory cache (fast)
            cached = lyrics_handler.get_from_cache(song, artist, album)
            if cached:
                logger.debug(f"Found lyrics in cache for '{song}'")
                return cached

            # If not in cache, fetch from service
            lyrics = lyrics_handler.fetch_lyrics(song, artist, album, duration)
            if lyrics:
                logger.info(f"Successfully fetched lyrics for '{song}'")
                # Store in cache (limit size to prevent memory bloat)
                lyrics_handler.store_in_cache(lyrics, song, artist, album)
                return lyrics
            else:
                logger.info(f"No lyrics found for '{song}'")
                return []
        except Exception as e:
            logger.error(f"Error fetching lyrics: {e}")
            return []

    # Launch the async fetch and track the future for cleanup
    future = thread_pool.submit(fetch_lyrics)

    # Track active futures for proper cleanup
    if active_futures is not None:
        active_futures.add(future)
        # Add done callback to remove future from tracking set
        future.add_done_callback(
            lambda f: active_futures.discard(f)
            if hasattr(active_futures, "discard")
            else None
        )

    return future


def get_lyrics_display(
    song: str,
    artist: str,
    album: str,
    elapsed: float,
    duration: float,
    metadata_ready: bool,
    lyrics_state: LyricsState,
    lyrics_handler: LyricsHandler,
) -> str:
    """
    Get lyrics display content for the current song and playback position.

    Args:
        song: Song name
        artist: Artist name
        album: Album name
        elapsed: Current playback position in seconds
        duration: Song duration in seconds
        metadata_ready: Whether metadata has been loaded
        lyrics_state: Current lyrics state object
        lyrics_handler: Lyrics handler instance

    Returns:
        Formatted lyrics display content
    """
    # Get theme-consistent header
    header = get_lyrics_header()

    # Check prerequisites
    if (
        lyrics_state.status == LyricsStatus.DISABLED
        or not lyrics_handler.has_lyrics_support()
    ):
        return f"{header}{format_feedback_message('Lyrics feature not available')}"

    if not metadata_ready:
        return f"{header}{format_feedback_message('Waiting for song metadata...')}"

    # Display logic for different scenarios
    if lyrics_state.status == LyricsStatus.AVAILABLE and lyrics_state.cached_lyrics:
        return f"{header}{format_cached_lyrics(song, artist, album, elapsed, lyrics_state, lyrics_handler)}"

    if lyrics_state.future and lyrics_state.future.done():
        return f"{header}{handle_completed_lyrics_fetch(song, artist, album, elapsed, lyrics_state, lyrics_handler)}"

    if (
        lyrics_state.status == LyricsStatus.LOADING
        and lyrics_state.future
        and not lyrics_state.future.done()
    ):
        return f"{header}{lyrics_handler.get_waiting_message()}"

    # No fetch in progress and no cached lyrics
    if (
        lyrics_state.status == LyricsStatus.NOT_FOUND
        and lyrics_state.no_lyrics_message is None
    ):
        lyrics_state.no_lyrics_message = lyrics_handler.get_no_lyrics_message()

    return f"{header}{lyrics_state.no_lyrics_message or 'No lyrics available'}"


def get_lyrics_header() -> str:
    """Get a theme-consistent lyrics section header."""
    theme_name = get_current_theme()
    theme_obj = get_theme(theme_name)

    from ...themes.adapters import get_gradient_styles

    theme_gradients = get_gradient_styles(theme_obj)
    lyrics_header_style = theme_gradients.get("primary")

    return f"\n\n[bold {lyrics_header_style}]󰇘󰇘󰇘󰇘 Lyrics 󰇘󰇘󰇘󰇘[/bold {lyrics_header_style}]\n"


def format_feedback_message(message: str) -> str:
    """Format a feedback message with theme-consistent styling."""
    from ..lyrics_handler import LyricsHandler

    # Create a temporary handler just for formatting
    temp_handler = LyricsHandler()
    feedback_text = temp_handler.apply_gradient_to_text(message, "feedback")
    return f"[italic]{feedback_text}[/italic]"


def format_cached_lyrics(
    song: str,
    artist: str,
    album: str,
    elapsed: float,
    lyrics_state: LyricsState,
    lyrics_handler: LyricsHandler,
) -> str:
    """
    Format cached lyrics for display.

    Args:
        song: Song name
        artist: Artist name
        album: Album name
        elapsed: Current playback position in seconds
        lyrics_state: Current lyrics state
        lyrics_handler: Lyrics handler instance

    Returns:
        Formatted lyrics text
    """
    # Safety check
    if not lyrics_state.cached_lyrics:
        return lyrics_handler.get_no_lyrics_message()

    # Determine lyrics type and display accordingly
    is_synced = lyrics_handler._is_synced_lyrics(lyrics_state.cached_lyrics)

    if is_synced:
        return lyrics_handler.create_focused_lyrics_view(
            lyrics_state.cached_lyrics, elapsed, song, artist, album
        )
    else:
        # For plain lyrics, use the gradient effect
        plain_lyrics = lyrics_handler._get_plain_lyrics(lyrics_state.cached_lyrics)
        return lyrics_handler._create_simple_gradient_view(plain_lyrics[:15])


def handle_completed_lyrics_fetch(
    song: str,
    artist: str,
    album: str,
    elapsed: float,
    lyrics_state: LyricsState,
    lyrics_handler: LyricsHandler,
) -> str:
    """
    Handle completed lyrics fetch operation.

    Args:
        song: Song name
        artist: Artist name
        album: Album name
        elapsed: Current playback position in seconds
        lyrics_state: Current lyrics state
        lyrics_handler: Lyrics handler instance

    Returns:
        Formatted lyrics display
    """
    try:
        lyrics = lyrics_state.future.result()

        if lyrics:
            lyrics_state.cached_lyrics = lyrics
            lyrics_state.status = LyricsStatus.AVAILABLE
            return format_cached_lyrics(
                song, artist, album, elapsed, lyrics_state, lyrics_handler
            )
        else:
            # Get a stable "no lyrics" message
            lyrics_state.status = LyricsStatus.NOT_FOUND
            if lyrics_state.no_lyrics_message is None:
                lyrics_state.no_lyrics_message = lyrics_handler.get_no_lyrics_message()
            return lyrics_state.no_lyrics_message

    except Exception as e:
        logger.error(f"Error retrieving lyrics: {e}")
        lyrics_state.status = LyricsStatus.NOT_FOUND
        return lyrics_handler.get_error_message(str(e))
