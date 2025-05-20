"""
YouTube Search Module

This module provides functionality for searching songs on YouTube with improved
organization, error handling, and maintainability.
"""

from ytmusicapi import YTMusic
from typing import List, Dict, Optional, Any, Protocol, NamedTuple, Tuple

from aurras.utils.logger import get_logger
from aurras.core.downloader import DownloadsDatabase
from aurras.core.player.history import RecentlyPlayedManager
from aurras.core.cache.search_db import SearchFromSongDataBase
from aurras.core.cache.updater import UpdateSearchHistoryDatabase
from aurras.utils.handle_fuzzy_search import FuzzySearcher, FuzzyDictMatcher

logger = get_logger("aurras.services.youtube.search", log_to_console=False)


class SongResult(NamedTuple):
    """Represents a single song search result."""

    name: str
    url: str
    thumbnail_url: str = ""
    artist: str = ""  # Artist field for better lyrics search
    album: str = ""  # Album field
    is_from_history: bool = False  # Flag to mark history songs


# Define interfaces for better separation
class SearchProvider(Protocol):
    """Interface for any search provider."""

    def search(self, queries: List[str]) -> List[SongResult]:
        """Search for songs."""
        ...


class CacheProvider(Protocol):
    """Interface for any cache provider."""

    def get_songs(self, queries: List[str]) -> Dict[str, SongResult]:
        """Get songs from cache."""
        ...

    def save_songs(self, query_to_song: Dict[str, SongResult]) -> None:
        """Save songs to cache."""
        ...

    def get_recent_songs(self, limit: int = 30) -> List[SongResult]:
        """Get recently played songs."""
        ...


# Implementation classes
class YouTubeSearchProvider:
    """Provider for YouTube song searches."""

    def __init__(self) -> None:
        self._temp_storage: Dict[str, SongResult] = {}

    def search(self, queries: List[str]) -> List[SongResult]:
        """Search for songs on YouTube."""
        results = []

        for query in queries:
            # Check temp storage first
            if query in self._temp_storage:
                results.append(self._temp_storage[query])
                continue

            # Search YouTube
            try:
                song_result = self._search_single_query(query)
                if song_result:
                    results.append(song_result)
                    self._temp_storage[query] = song_result
            except Exception as e:
                logger.error(f"Error searching YouTube for '{query}': {e}")

        return results

    def _search_single_query(self, query: str) -> Optional[SongResult]:
        """Search for a single query on YouTube."""
        try:
            with YTMusic() as ytmusic:
                results = ytmusic.search(query, filter="songs", limit=1)

                if not results:
                    logger.warning(f"No results found for: {query}")
                    return None

                song_data = results[0]
                video_id = song_data.get("videoId")

                if not video_id:
                    logger.warning(f"No video ID found for: {query}")
                    return None

                title = song_data.get("title", "Unknown Song")
                artist = (
                    song_data.get("artists", [{}])[0].get("name", "Unknown Artist")
                    if song_data.get("artists")
                    else "Unknown Artist"
                )

                # Extract album information if available
                album = "Unknown Album"
                if "album" in song_data and song_data["album"]:
                    album = song_data["album"].get("name", "Unknown Album")

                url = f"https://www.youtube.com/watch?v={video_id}"

                # Get thumbnail if available
                thumbnail_url = ""
                if "thumbnails" in song_data and song_data["thumbnails"]:
                    thumbnail_url = song_data["thumbnails"][0]["url"]

                return SongResult(title, url, thumbnail_url, artist, album)

        except Exception as e:
            logger.error(f"YTMusic API error for '{query}': {e}")
            raise


class DatabaseCacheProvider:
    """Provider for database caching of song searches."""

    def __init__(self) -> None:
        self.updater = UpdateSearchHistoryDatabase()
        self.search_db = SearchFromSongDataBase()
        self.downloads_db = DownloadsDatabase()
        self.history_manager = RecentlyPlayedManager()
        self.fuzzy_search = FuzzySearcher(threshold=0.56)
        self.fuzzy_dict_matcher = FuzzyDictMatcher(threshold=0.47)

    def get_songs(self, queries: List[str]) -> Dict[str, SongResult]:
        """Get songs from the database cache."""
        result = {}

        cache_dict = self.search_db.initialize_full_song_dict()
        downloads_dict = self.downloads_db.get_downloaded_songs()
        song_dict = self.fuzzy_dict_matcher.merge_song_databases(
            cache_dict, downloads_dict
        )  # Instead of using update method, we use our enhanced merge method
        logger.debug(f"Retrieved {len(song_dict)} songs from cache dictionary")

        for query in queries:
            # convert the query to actual song name that might be present in cache
            query_corrected = self.fuzzy_search.find_best_match(
                query, list(song_dict.keys())
            )
            if query_corrected is None:
                return result

            song_info = song_dict[query_corrected]

            result[query] = SongResult(
                name=song_info["track_name"],
                url=song_info["url"],
                thumbnail_url=song_info.get("thumbnail_url", ""),
                artist=song_info.get("artist_name", ""),
                album=song_info.get("album_name", ""),
            )

        return result

    def save_songs(self, query_to_song: Dict[str, SongResult]) -> None:
        """Save songs with complete metadata to the database cache."""
        try:
            # Get existing songs to avoid duplicates
            existing_songs = self.search_db.initialize_full_song_dict()

            for query, song in query_to_song.items():
                # Check if this song already exists in the cache
                exists = False

                # Check by URL (most reliable way to identify duplicates)
                for _, cache_song in existing_songs.items():
                    if (cache_song.get("url") == song.url and song.url) or (
                        cache_song.get("track_name") == song.name
                        and cache_song.get("artist_name") == song.artist
                        and song.name
                        and song.artist
                    ):
                        exists = True
                        logger.debug(
                            f"Song already in cache: {song.name} by {song.artist}"
                        )
                        break

                # Only save if the song doesn't exist
                if not exists:
                    # Use the enhanced save method with consistent field names
                    self.updater.save_to_cache(
                        song_user_searched=query,
                        track_name=song.name,
                        url=song.url,
                        artist_name=song.artist,
                        album_name=song.album,
                        thumbnail_url=song.thumbnail_url,
                        duration=0,  # We don't have duration from YouTube search
                    )
                    logger.debug(
                        f"Cached new song: {query} -> {song.name} by {song.artist}"
                    )
        except Exception as e:
            logger.warning(f"Failed to update search cache: {str(e)}")

    def get_recent_songs(self, limit: int = 30) -> List[SongResult]:
        """
        Get recently played songs from history.

        Args:
            limit: Maximum number of recent songs to return

        Returns:
            List of recent songs from history as SongResult objects
        """
        try:
            # Get recent songs from the history manager
            recent_songs = self.history_manager.get_recent_songs(limit)
            logger.debug(f"Retrieved {len(recent_songs)} songs from history")

            # Get song details from database for URLs
            song_dict = self.search_db.initialize_song_dict()
            logger.debug(f"Retrieved {len(song_dict)} songs from cache dictionary")

            # Create a set to track seen songs to avoid duplicates
            seen_songs = set()
            results = []
            missing_urls = []

            # Process recent songs and find their URLs
            for song_record in recent_songs:
                song_name = song_record["song_name"]

                # Skip duplicates
                if song_name in seen_songs:
                    continue

                seen_songs.add(song_name)

                # Find URL in dictionary (matching by song name)
                url = None
                for query, (name, song_url) in song_dict.items():
                    if name.lower() == song_name.lower():  # Case-insensitive comparison
                        url = song_url
                        break

                # If we found a URL, add to results
                if url:
                    results.append(SongResult(song_name, url, is_from_history=True))
                else:
                    # Keep track of songs with missing URLs for logging
                    missing_urls.append(song_name)

                    # Fall back to using the song name as search query for immediate playback
                    # Create a temporary YouTube search just for this song
                    try:
                        temp_search = SongSearch()
                        temp_results = temp_search.search(
                            song_name, include_history=False
                        )
                        if temp_results:
                            # Use the first result as fallback
                            results.append(
                                SongResult(
                                    song_name,
                                    temp_results[0].url,
                                    temp_results[0].thumbnail_url,
                                    temp_results[0].artist
                                    if hasattr(temp_results[0], "artist")
                                    else "",
                                    temp_results[0].album
                                    if hasattr(temp_results[0], "album")
                                    else "",
                                    is_from_history=True,
                                )
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to find URL for history song '{song_name}': {e}"
                        )

            if missing_urls:
                logger.warning(
                    f"Could not find URLs for {len(missing_urls)} history songs: {missing_urls[:5]}..."
                )

            logger.debug(f"Found {len(results)} songs with URLs in history")
            return results

        except Exception as e:
            logger.error(f"Failed to get recent songs: {str(e)}")
            return []


class SongSearch:
    """Main search coordinator that combines multiple search providers."""

    def __init__(
        self,
        cache_provider: Optional[CacheProvider] = None,
        search_provider: Optional[SearchProvider] = None,
    ) -> None:
        """Initialize with optional providers (for easier testing)."""
        self.cache_provider = cache_provider or DatabaseCacheProvider()
        self.search_provider = search_provider or YouTubeSearchProvider()
        self.results: List[SongResult] = []
        self.history_results: List[SongResult] = []
        self.queue_start_index: int = (
            0  # Index where searched songs start in combined results
        )

    def search(
        self,
        queries: List[str] | str,
        include_history: bool = True,
        history_limit: int = 30,
    ) -> List[SongResult]:
        """
        Search for songs across all available sources.

        Args:
            queries: One or more search terms
            include_history: Whether to include history songs before searched songs
            history_limit: Maximum number of history songs to include

        Returns:
            List of song results (history + searched songs)
        """
        # Normalize input to list
        if isinstance(queries, str):
            queries = [queries]

        self.results = []
        self.history_results = []

        try:
            # Get history if requested
            if include_history:
                logger.info(f"Including up to {history_limit} history songs in queue")
                self.history_results = self.cache_provider.get_recent_songs(
                    history_limit
                )
                logger.info(f"Added {len(self.history_results)} history songs to queue")

                # Debug output to verify ordering
                if self.history_results:
                    history_samples = [r.name for r in self.history_results[:3]]
                    logger.debug(f"History song samples: {', '.join(history_samples)}")

            # Set queue start index to length of history
            self.queue_start_index = len(self.history_results)
            logger.debug(f"Queue will start at index {self.queue_start_index}")

            # First check cache for searched songs
            cached_songs = self.cache_provider.get_songs(queries)

            # Track which queries need online search
            queries_to_search = []
            query_to_result = {}

            # Process cached results
            for query in queries:
                if query in cached_songs:
                    self.results.append(cached_songs[query])
                    logger.debug(f"Found in cache: {query}")
                # elif query in downloads
                else:
                    queries_to_search.append(query)

            # If we have queries that need searching
            if queries_to_search:
                logger.info(f"Searching online for {len(queries_to_search)} songs")
                online_results = self.search_provider.search(queries_to_search)

                # Match results back to queries for caching
                if len(online_results) == len(queries_to_search):
                    for i, result in enumerate(online_results):
                        query = queries_to_search[i]
                        query_to_result[query] = result

                # Update cache with new results
                if query_to_result:
                    self.cache_provider.save_songs(query_to_result)

                # Add online results to final results
                self.results.extend(online_results)

            # Combine history with search results
            combined_results = self.history_results + self.results

            # Debug output to verify final ordering
            if combined_results:
                start_examples = [
                    r.name for r in combined_results[: min(3, len(combined_results))]
                ]
                if self.queue_start_index < len(combined_results):
                    searched_examples = [
                        r.name
                        for r in combined_results[
                            self.queue_start_index : self.queue_start_index + 3
                        ]
                    ]
                    logger.debug(f"First items in queue: {', '.join(start_examples)}")
                    logger.debug(
                        f"First searched items: {', '.join(searched_examples)}"
                    )

            logger.info(
                f"Found {len(self.results)} searched songs and {len(self.history_results)} history songs"
            )
            return combined_results

        except Exception as e:
            logger.error(f"Error during song search: {str(e)}")
            raise

    def get_playback_info(self) -> Tuple[List[SongResult], int]:
        """
        Get combined results and the index to start playback from.

        Returns:
            Tuple containing the combined list of songs and the index to start playback from
        """
        combined_results = self.history_results + self.results
        return combined_results, self.queue_start_index

    @property
    def song_names(self) -> List[str]:
        """Get a list of song names from the search results (no history)."""
        return [result.name for result in self.results]

    @property
    def song_urls(self) -> List[str]:
        """Get a list of song URLs from the search results (no history)."""
        return [result.url for result in self.results]

    @property
    def song_thumbnails(self) -> List[str]:
        """Get a list of song thumbnail URLs from the search results (no history)."""
        return [result.thumbnail_url for result in self.results]

    @property
    def all_song_names(self) -> List[str]:
        """Get a list of all song names including history."""
        return [result.name for result in self.history_results + self.results]

    @property
    def all_song_urls(self) -> List[str]:
        """Get a list of all song URLs including history."""
        return [result.url for result in self.history_results + self.results]

    @property
    def all_song_thumbnails(self) -> List[str]:
        """Get a list of all song thumbnail URLs including history."""
        return [result.thumbnail_url for result in self.history_results + self.results]


# Maintain backward compatibility
class SongMetadata:
    """Base class for storing and managing song metadata (for backward compatibility)."""

    def __init__(self) -> None:
        self.song_name_searched: List[str] = []
        self.song_url_searched: List[str] = []
        self.song_thumbnail_url: List[str] = []
        # New properties for history and queue management
        self.history_songs: List[str] = []
        self.history_urls: List[str] = []
        self.queue_start_index: int = 0


class SearchFromYoutube(SongMetadata):
    """Class for searching songs directly from YouTube (for backward compatibility)."""

    def __init__(self, search_queries: List[str]) -> None:
        """
        Initialize YouTube search with search queries.

        Args:
            search_queries: List of song names to search for on YouTube
        """
        super().__init__()
        self.search_queries = search_queries
        self.temporary_metadata_storage: Dict[str, str] = {}

    def search_from_youtube(self) -> None:
        """
        Search for all queries on YouTube and extract song metadata.
        Handles both new searches and retrieving from temporary storage.
        """
        try:
            # Clear previous results to avoid appending to old data
            self.song_name_searched = []
            self.song_url_searched = []
            self.song_thumbnail_url = []

            # Check for existing songs in temporary storage
            for query in self.search_queries:
                cached_url = self._get_temporary_url(query)
                if cached_url:
                    # Use cached data
                    logger.debug(f"Using cached result for: {query}")
                    self.song_name_searched.append(query)
                    self.song_url_searched.append(cached_url)
                else:
                    # Search YouTube for new songs
                    logger.debug(f"Searching YouTube for: {query}")
                    self._search_and_extract_song_metadata(query)

            logger.info(f"Found {len(self.song_name_searched)} songs on YouTube")
        except Exception as e:
            logger.error(f"YouTube search failed: {str(e)}")
            # Re-raise as we want to propagate the error
            raise

    def _search_and_extract_song_metadata(self, query: str) -> None:
        """
        Search for a single query on YouTube and extract its metadata.

        Args:
            query: Song name to search for
        """
        search_results = self._execute_youtube_search(query)
        if not search_results:
            logger.warning(f"No results found for: {query}")
            return

        # Extract metadata from search result
        song_metadata = search_results[0]
        video_id = song_metadata.get("videoId")
        title = song_metadata.get("title", "Unknown Song")

        if not video_id:
            logger.warning(f"No video ID found for: {query}")
            return

        # Get thumbnail URL if available
        thumbnail_url = ""
        if "thumbnails" in song_metadata and song_metadata["thumbnails"]:
            thumbnail_url = song_metadata["thumbnails"][0]["url"]

        # Construct YouTube URL
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"

        # Store the results
        self.song_name_searched.append(title)
        self.song_url_searched.append(youtube_url)
        if thumbnail_url:
            self.song_thumbnail_url.append(thumbnail_url)

        # Update temporary storage
        self._update_temporary_storage(title, youtube_url)

    def _execute_youtube_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute the actual YouTube search.

        Args:
            query: Song name to search for

        Returns:
            List of search results from YTMusic API
        """
        try:
            with YTMusic() as ytmusic:
                results = ytmusic.search(query, filter="songs", limit=1)
                return results if results else []
        except Exception as e:
            logger.error(f"YTMusic API error for '{query}': {str(e)}")
            return []

    def _update_temporary_storage(self, song_name: str, song_url: str) -> None:
        """
        Update temporary storage with song name and URL.

        Args:
            song_name: Name of the song
            song_url: URL of the song
        """
        self.temporary_metadata_storage[song_name] = song_url
        # Also store with original query as key for better matching
        if self.search_queries and len(self.song_name_searched) <= len(
            self.search_queries
        ):
            idx = len(self.song_name_searched) - 1
            if idx >= 0 and idx < len(self.search_queries):
                self.temporary_metadata_storage[self.search_queries[idx]] = song_url

    def _get_temporary_url(self, song_name: str) -> Optional[str]:
        """
        Get URL for a song from temporary storage.

        Args:
            song_name: Name of the song to find

        Returns:
            URL of the song if found, None otherwise
        """
        return self.temporary_metadata_storage.get(song_name)


class SearchSong(SongMetadata):
    """
    Primary song search class that combines database and YouTube searches.
    """

    def __init__(self, search_queries: List[str]) -> None:
        super().__init__()
        self.update_song_history = UpdateSearchHistoryDatabase()
        self.search_from_db = SearchFromSongDataBase()

        # Use the new implementation under the hood
        self.search_queries = (
            search_queries if isinstance(search_queries, list) else [search_queries]
        )
        self._new_search = SongSearch()
        self.search_from_yt = SearchFromYoutube(self.search_queries)
        self.include_history = True  # Default to including history

    def search_song(
        self, include_history: bool = True, history_limit: int = 20
    ) -> None:
        """
        Main search method using the new implementation.

        Args:
            include_history: Whether to include history songs in the queue
            history_limit: Maximum number of history songs to include
        """
        try:
            logger.info(
                f"Searching for songs with history={include_history}, limit={history_limit}"
            )

            # Store the setting
            self.include_history = include_history

            # Search with history included
            combined_results = self._new_search.search(
                self.search_queries,
                include_history=include_history,
                history_limit=history_limit,
            )

            # Store the queue start index
            self.queue_start_index = self._new_search.queue_start_index
            logger.info(
                f"Queue will start at index {self.queue_start_index} of {len(combined_results)} total songs"
            )

            # Update the old-style properties for backward compatibility
            if include_history and self.queue_start_index > 0:
                # Store history separately
                self.history_songs = [
                    r.name for r in combined_results[: self.queue_start_index]
                ]
                self.history_urls = [
                    r.url for r in combined_results[: self.queue_start_index]
                ]

                # Log first few history songs
                if self.history_songs:
                    logger.debug(
                        f"First few history songs: {', '.join(self.history_songs[:3])}"
                    )

                # Store searched songs
                self.song_name_searched = [
                    r.name for r in combined_results[self.queue_start_index :]
                ]
                self.song_url_searched = [
                    r.url for r in combined_results[self.queue_start_index :]
                ]

                # Log first few searched songs
                if self.song_name_searched:
                    logger.debug(
                        f"First few searched songs: {', '.join(self.song_name_searched[:3])}"
                    )

                # Also store thumbnails if available
                self.song_thumbnail_url = [
                    r.thumbnail_url
                    for r in combined_results[self.queue_start_index :]
                    if r.thumbnail_url
                ]
                logger.info(
                    f"Added {len(self.history_songs)} history songs and {len(self.song_name_searched)} searched songs"
                )
            else:
                # Just store the search results (no history)
                self.song_name_searched = [r.name for r in combined_results]
                self.song_url_searched = [r.url for r in combined_results]
                self.song_thumbnail_url = [
                    r.thumbnail_url for r in combined_results if r.thumbnail_url
                ]
                logger.info(
                    f"Added {len(self.song_name_searched)} searched songs (no history)"
                )
        except Exception as e:
            logger.error(f"Error during song search: {str(e)}")
            raise

    def get_all_queued_songs(self) -> Tuple[List[str], List[str], int]:
        """
        Get all songs for the queue (history + searched) and the starting index.

        Returns:
            Tuple containing lists of all song names, URLs, and the index to start playback from
        """
        all_songs = self.history_songs + self.song_name_searched
        all_urls = self.history_urls + self.song_url_searched
        logger.info(
            f"Returning complete queue with {len(all_songs)} songs, starting at {self.queue_start_index}"
        )
        return all_songs, all_urls, self.queue_start_index
