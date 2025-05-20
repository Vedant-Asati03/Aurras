import re
from functools import lru_cache
from typing import List, Optional
from difflib import SequenceMatcher
from aurras.utils.logger import get_logger

logger = get_logger("aurras.utils.handle_fuzzy_search", log_to_console=False)


class FuzzySearcher:
    """
    Enhanced fuzzy search implementation tailored for music searches.
    Provides music-specific optimizations and multiple search algorithms.
    """

    def __init__(self, threshold=0.6, use_cache=True, music_mode=True):
        """
        Initialize the fuzzy searcher with configurable parameters.

        Args:
            threshold (float): Minimum similarity score (0-1) to consider a match
            use_cache (bool): Whether to use caching for performance
            music_mode (bool): Enable music-specific optimizations
        """
        self.threshold = threshold
        self.use_cache = use_cache
        self.music_mode = music_mode

        # Apply caching if enabled
        if use_cache:
            self._normalize = lru_cache(maxsize=10000)(self._normalize)
            self.similarity = lru_cache(maxsize=10000)(self.similarity)

        # Compile common music patterns for faster replacement
        if music_mode:
            self._music_patterns = [
                (re.compile(r"\(official\s+video\)", re.IGNORECASE), ""),
                (re.compile(r"\(official\s+audio\)", re.IGNORECASE), ""),
                (re.compile(r"\(official\s+music\s+video\)", re.IGNORECASE), ""),
                (re.compile(r"\(lyrics\)", re.IGNORECASE), ""),
                (re.compile(r"\(lyric\s+video\)", re.IGNORECASE), ""),
                (re.compile(r"\(audio\)", re.IGNORECASE), ""),
                (re.compile(r"\(visualizer\)", re.IGNORECASE), ""),
                (re.compile(r"\[official\]", re.IGNORECASE), ""),
                (re.compile(r"feat\.", re.IGNORECASE), "ft."),
                (re.compile(r"featuring", re.IGNORECASE), "ft."),
                (re.compile(r"\s+ft\.\s+", re.IGNORECASE), " ft. "),
                (re.compile(r"official\s+music\s+video", re.IGNORECASE), ""),
            ]

    def _normalize(self, text):
        """
        Normalize text for better matching with music-specific optimizations.

        Args:
            text (str): Input text

        Returns:
            str: Normalized text
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Apply music-specific optimizations if enabled
        if self.music_mode:
            # Remove common music video suffixes
            for pattern, replacement in self._music_patterns:
                text = pattern.sub(replacement, text)

        # Remove special characters but keep spaces
        text = re.sub(r"[^\w\s]", "", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def similarity(self, query, track_name):
        """
        Calculate similarity between query and track name.

        Args:
            query (str): User search query
            track_name (str): Actual track name to compare against

        Returns:
            float: Similarity score between 0 and 1
        """
        norm_query = self._normalize(query)
        norm_track = self._normalize(track_name)

        if not norm_query or not norm_track:
            return 0.0

        # Check for exact match first (case insensitive)
        if norm_query == norm_track:
            return 1.0

        # Check if normalized query is a subset of track name (for partial matches)
        if norm_query in norm_track:
            # Calculate how much of the track name matches the query
            return 0.75 + (len(norm_query) / len(norm_track) * 0.25)

        # Use SequenceMatcher for similarity calculation
        return SequenceMatcher(None, norm_query, norm_track).ratio()

    def is_match(self, query, track_name) -> bool:
        """
        Determine if query matches track name based on threshold.

        Args:
            query (str): User search query
            track_name (str): Actual track name to compare against

        Returns:
            bool: True if similarity score is above threshold
        """
        return self.similarity(query, track_name) >= self.threshold

    def find_best_match(self, query: str, track_names: List[str]) -> Optional[str]:
        """
        Find the single best match for a query from a list of track names.

        Args:
            query (str): User search query
            track_names (list): List of track names to search through

        Returns:
            str: The best matching track name, or None if no matches found
        """
        if not track_names:
            return None

        # If query exactly matches one of the tracks, return it immediately
        for track in track_names:
            if self._normalize(query) == self._normalize(track):
                return track

        # Otherwise, calculate similarity for all tracks
        best_match = None
        best_score = 0

        for track in track_names:
            score = self.similarity(query, track)
            if score > best_score:
                best_score = score
                best_match = track

        # Only return if the match meets our threshold
        if best_score >= self.threshold:
            return best_match

        return None

    def find_best_match_with_score(self, query, track_names):
        """
        Find the single best match for a query and return with its score.

        Args:
            query (str): User search query
            track_names (list): List of track names to search through

        Returns:
            tuple: (best_matching_track, score) or (None, 0) if no matches found
        """
        if not track_names:
            return None, 0

        best_match = None
        best_score = 0

        for track in track_names:
            score = self.similarity(query, track)
            if score > best_score:
                best_score = score
                best_match = track

        # Only return if the match meets our threshold
        if best_score >= self.threshold:
            return best_match, best_score

        return None, 0

    def search(self, query, track_names):
        """
        Search for query across multiple track names.

        Args:
            query (str): User search query
            track_names (list): List of track names to search through

        Returns:
            list: Sorted list of (track_name, score) tuples for matches above threshold
        """
        # For backward compatibility, keeping the original implementation
        results = []

        for track in track_names:
            score = self.similarity(query, track)
            if score >= self.threshold:
                results.append((track, score))

        # Sort by similarity score in descending order
        return sorted(results, key=lambda x: x[1], reverse=True)

    def search_songs(self, query, song_data, metadata_keys=None):
        """
        Specialized search for song dictionaries with metadata support.

        Args:
            query (str): User search query
            song_data (dict): Dictionary of songs with metadata
            metadata_keys (dict): Mapping of metadata keys to weight in search
                                 (e.g. {"track_name": 1.0, "artist_name": 0.7})

        Returns:
            list: Sorted list of (song_key, score, song_data) tuples
        """
        if metadata_keys is None:
            # Default weights for song metadata
            metadata_keys = {
                "track_name": 1.0,
                "title": 1.0,  # Alternative key
                "artist_name": 0.7,
                "artist": 0.7,  # Alternative key
                "album_name": 0.5,
                "album": 0.5,  # Alternative key
            }

        results = []

        # Search through each song
        for song_key, song_info in song_data.items():
            max_score = 0.0

            # Try matching against each metadata field
            for field, weight in metadata_keys.items():
                if field in song_info and song_info[field]:
                    field_value = str(song_info[field])
                    score = self.similarity(query, field_value) * weight
                    max_score = max(max_score, score)

            # Also check for combined matches (e.g. "artist - title")
            artist = song_info.get("artist_name", song_info.get("artist", ""))
            title = song_info.get("track_name", song_info.get("title", ""))

            if artist and title:
                combined = f"{artist} - {title}"
                combined_score = (
                    self.similarity(query, combined) * 0.9
                )  # Slightly lower weight
                max_score = max(max_score, combined_score)

            if max_score >= self.threshold:
                results.append((song_key, max_score, song_info))

        # Sort by score in descending order
        return sorted(results, key=lambda x: x[1], reverse=True)

    def get_best_matches(self, query, song_data, limit=5, metadata_keys=None):
        """
        Get the best matches for a query from song data.

        Args:
            query (str): User search query
            song_data (dict): Dictionary of songs with metadata
            limit (int): Maximum number of results to return
            metadata_keys (dict): Mapping of metadata keys to weight in search

        Returns:
            list: List of best matching song info dictionaries
        """
        results = self.search_songs(query, song_data, metadata_keys)

        # Log the top matches for debugging
        if results:
            logger.debug(
                f"Top match for '{query}': {results[0][0]} (score: {results[0][1]:.2f})"
            )

        # Return just the song info dictionaries, limited to the requested number
        return [info for _, _, info in results[:limit]]

    @classmethod
    def create_thread_safe_instance(cls, **kwargs):
        """
        Create a thread-safe instance with its own cache.
        Use this when you need to use the fuzzy searcher in different threads.

        Args:
            **kwargs: Arguments to pass to the constructor

        Returns:
            FuzzySearcher: A fresh instance for thread-safe use
        """
        return cls(**kwargs)


class FuzzyDictMatcher:
    """
    A specialized dictionary matcher optimized for Aurras music database operations.
    Specifically designed for merging cache_dict and downloads_dict while handling
    the unique structure of song metadata.
    """

    def __init__(self, threshold=0.7, use_cache=True, music_mode=True):
        """
        Initialize the fuzzy dictionary matcher with Aurras-specific optimizations.

        Args:
            threshold (float): Minimum similarity score (0-1) to consider a match
            use_cache (bool): Whether to use caching for performance
            music_mode (bool): Enable music-specific optimizations
        """
        self.threshold = threshold
        self.use_cache = use_cache
        self.music_mode = music_mode

        self._normalize = (
            lru_cache(maxsize=10000)(self._normalize) if use_cache else self._normalize
        )
        self.similarity = (
            lru_cache(maxsize=10000)(self.similarity) if use_cache else self.similarity
        )

        # Music-specific patterns for normalization - optimized for Aurras database format
        if music_mode:
            self._music_patterns = [
                # Movie soundtrack patterns (very common in your data)
                (
                    re.compile(
                        r"\s*[\(\[](From|from)(\s+\"|\s+\')?(.+?)(\"|\')?[\)\]]",
                        re.IGNORECASE,
                    ),
                    "",
                ),
                (
                    re.compile(
                        r"\s*-\s*From(\s+\"|\s+\')?(.+?)(\"|\')?[\)\]]", re.IGNORECASE
                    ),
                    "",
                ),
                # Common video suffixes
                (re.compile(r"\(official\s+video\)", re.IGNORECASE), ""),
                (re.compile(r"\(official\s+audio\)", re.IGNORECASE), ""),
                (re.compile(r"\(lyrics\)", re.IGNORECASE), ""),
                # Featured artist patterns
                (re.compile(r"\(feat\..*?\)", re.IGNORECASE), ""),
                (re.compile(r"\(ft\..*?\)", re.IGNORECASE), ""),
                (re.compile(r"\s+feat\..*?$", re.IGNORECASE), ""),
                (re.compile(r"\s+ft\..*?$", re.IGNORECASE), ""),
                # General cleanup
                (re.compile(r"\[.*?\]", re.IGNORECASE), ""),
                (re.compile(r"feat\.", re.IGNORECASE), "ft."),
                (re.compile(r"ft\.\s+", re.IGNORECASE), "ft. "),
                (
                    re.compile(r"\s+-\s+", re.IGNORECASE),
                    " ",
                ),  # Replace " - " with space
            ]

        # Define metadata field mapping for Aurras database structure
        self.track_fields = ["track_name", "title", "name", "song"]
        self.artist_fields = ["artist_name", "artist", "singer", "performer"]
        self.album_fields = ["album_name", "album"]
        self.url_fields = ["url", "file_path"]

        # Fields to prioritize from downloads_dict (local files)
        self.priority_fields = ["url", "duration", "thumbnail_url"]

    def _normalize(self, text):
        """
        Normalize text specifically for Aurras song database matching.

        Args:
            text: Input text to normalize

        Returns:
            Normalized text string
        """
        if not isinstance(text, str):
            return str(text)

        # Convert to lowercase
        text = text.lower()

        # Apply music-specific patterns
        if self.music_mode:
            # Remove parts that don't contribute to matching
            for pattern, replacement in self._music_patterns:
                text = pattern.sub(replacement, text)

            # Special handling for artists list (common in your data)
            if "," in text and len(text) > 30:
                # If text looks like an artist list with song title, keep only the song title part
                if " - " in text:
                    text = text.split(" - ")[-1]

            # Remove common file extensions that might appear in downloads_dict
            text = re.sub(r"\.mp3$", "", text)
            text = re.sub(r"\.m4a$", "", text)
            text = re.sub(r"\.wav$", "", text)

        # Remove special characters but keep spaces
        text = re.sub(r"[^\w\s]", "", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def similarity(self, str1, str2):
        """
        Calculate similarity between two strings with optimizations for song titles.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score between 0 and 1
        """
        norm_str1 = self._normalize(str1)
        norm_str2 = self._normalize(str2)

        if not norm_str1 or not norm_str2:
            return 0.0

        # Check for exact match after normalization
        if norm_str1 == norm_str2:
            return 1.0

        # Check if one is a significant substring of the other
        if len(norm_str1) > 5 and norm_str1 in norm_str2:
            # Calculate how much of str2 is covered by str1
            coverage = len(norm_str1) / len(norm_str2)
            # Higher score for better coverage
            return 0.75 + (coverage * 0.25)

        if len(norm_str2) > 5 and norm_str2 in norm_str1:
            coverage = len(norm_str2) / len(norm_str1)
            return 0.75 + (coverage * 0.25)

        # Standard sequence matching
        return SequenceMatcher(None, norm_str1, norm_str2).ratio()

    def merge_song_databases(self, cache_dict, downloads_dict, prefer_downloads=True):
        """
        Merge cache_dict and downloads_dict with smart duplicate handling.
        Specifically designed for the Aurras database structure.

        Args:
            cache_dict: Dictionary of cached songs from search_db
            downloads_dict: Dictionary of downloaded songs
            prefer_downloads: Whether to prioritize downloaded song metadata

        Returns:
            dict: Merged song dictionary with best metadata from both sources
        """
        result = cache_dict.copy()

        # First add any downloaded songs not in cache
        downloads_added = 0
        for dl_key, dl_data in downloads_dict.items():
            # Check if this exact key exists
            if dl_key in result:
                # Merge metadata, preferring downloads for specified fields
                result[dl_key] = self._merge_song_metadata(
                    result[dl_key], dl_data, prefer_second=prefer_downloads
                )
                continue

            # Look for similar keys
            best_match, best_score = self._find_best_key_match(dl_key, result)

            if best_match and best_score >= self.threshold:
                # Merge with existing entry
                result[best_match] = self._merge_song_metadata(
                    result[best_match], dl_data, prefer_second=prefer_downloads
                )
                # Optionally update the key if download key is better
                if prefer_downloads and self._is_better_key(dl_key, best_match):
                    result[dl_key] = result.pop(best_match)
            else:
                # No match found, add new entry
                result[dl_key] = dl_data
                downloads_added += 1

        logger.debug(
            f"Merged song databases: added {downloads_added} new downloaded songs"
        )
        return result

    def _find_best_key_match(self, key, target_dict):
        """
        Find the best matching key in the target dictionary.

        Args:
            key: Key to find a match for
            target_dict: Dictionary to search in

        Returns:
            tuple: (best_matching_key, score) or (None, 0) if no match
        """
        best_match = None
        best_score = 0

        # Extract track name from the key's metadata if available
        key_track_name = None
        if key in target_dict and any(
            field in target_dict[key] for field in self.track_fields
        ):
            for field in self.track_fields:
                if field in target_dict[key] and target_dict[key][field]:
                    key_track_name = target_dict[key][field]
                    break

        for target_key in target_dict:
            # Calculate direct key similarity
            key_sim = self.similarity(key, target_key)

            # If we have track_name metadata, also check that
            meta_sim = 0
            if key_track_name:
                # Find track name in target metadata
                target_track_name = None
                if any(field in target_dict[target_key] for field in self.track_fields):
                    for field in self.track_fields:
                        if (
                            field in target_dict[target_key]
                            and target_dict[target_key][field]
                        ):
                            target_track_name = target_dict[target_key][field]
                            break

                if target_track_name:
                    meta_sim = self.similarity(key_track_name, target_track_name)

            # Use the better of the two scores
            score = max(key_sim, meta_sim)

            if score > best_score:
                best_score = score
                best_match = target_key

        return best_match, best_score

    def _is_better_key(self, key1, key2):
        """
        Determine if key1 is a better song key than key2.
        Prefers shorter, cleaner keys without artist lists.

        Args:
            key1: First key
            key2: Second key

        Returns:
            bool: True if key1 is better than key2
        """
        norm1 = self._normalize(key1)
        norm2 = self._normalize(key2)

        # Prefer keys without multiple artists (indicated by commas)
        if "," in key2 and "," not in key1:
            return True
        if "," in key1 and "," not in key2:
            return False

        # Prefer keys without "From..." or soundtrack mentions
        if "from" in norm2 and "from" not in norm1:
            return True
        if "from" in norm1 and "from" not in norm2:
            return False

        # Generally prefer shorter keys as they're cleaner
        return len(norm1) < len(norm2)

    def _merge_song_metadata(self, primary, secondary, prefer_second=False):
        """
        Merge song metadata dictionaries with special handling for Aurras fields.

        Args:
            primary: Primary metadata dict
            secondary: Secondary metadata dict
            prefer_second: Whether to prefer values from secondary dict

        Returns:
            dict: Merged metadata dictionary
        """
        result = primary.copy()

        # Always use local URL from downloads_dict if available
        if "url" in secondary and secondary["url"] and secondary["url"].startswith("/"):
            result["url"] = secondary["url"]

        # Process priority fields (often better in downloads_dict)
        for field in self.priority_fields:
            if field in secondary and secondary[field]:
                if field not in primary or not primary[field] or prefer_second:
                    result[field] = secondary[field]

        # Process all other fields
        for key, value in secondary.items():
            if key not in self.priority_fields and value:
                if key not in primary or not primary[key] or prefer_second:
                    result[key] = value

        return result

    def is_local_file(self, song_info):
        """
        Check if a song entry refers to a local file.

        Args:
            song_info: Song metadata dictionary

        Returns:
            bool: True if the song is a local file
        """
        if "url" in song_info and isinstance(song_info["url"], str):
            url = song_info["url"]
            # Check if it's a local path (starts with / or ./)
            return url.startswith("/") or url.startswith("./") or " " in url
        return False

    def deduplicate_songs(self, song_dict, prefer_local=True):
        """
        Remove duplicate songs from the dictionary.

        Args:
            song_dict: Dictionary of songs
            prefer_local: Whether to prefer local files when deduplicating

        Returns:
            dict: Deduplicated song dictionary
        """
        # Group similar songs
        groups = {}
        processed_keys = set()

        # First pass: group by track name
        for key, data in song_dict.items():
            if key in processed_keys:
                continue

            track_name = None
            for field in self.track_fields:
                if field in data and data[field]:
                    track_name = data[field]
                    break

            if not track_name:
                continue

            # Create a new group
            norm_track = self._normalize(track_name)
            if norm_track not in groups:
                groups[norm_track] = []

            groups[norm_track].append((key, data))
            processed_keys.add(key)

            # Find similar entries
            for other_key, other_data in song_dict.items():
                if other_key in processed_keys:
                    continue

                other_track = None
                for field in self.track_fields:
                    if field in other_data and other_data[field]:
                        other_track = other_data[field]
                        break

                if not other_track:
                    continue

                if self.similarity(track_name, other_track) >= self.threshold:
                    groups[norm_track].append((other_key, other_data))
                    processed_keys.add(other_key)

        # Second pass: select the best entry from each group
        result = {}
        for group in groups.values():
            if not group:
                continue

            if len(group) == 1:
                # Only one entry, keep it
                key, data = group[0]
                result[key] = data
                continue

            # Multiple entries, select the best one
            best_key, best_data = self._select_best_entry(group, prefer_local)
            result[best_key] = best_data

        return result

    def _select_best_entry(self, entries, prefer_local=True):
        """
        Select the best entry from a group of similar songs.

        Args:
            entries: List of (key, data) tuples
            prefer_local: Whether to prefer local files

        Returns:
            tuple: (best_key, best_data)
        """
        if not entries:
            return None, None

        if len(entries) == 1:
            return entries[0]

        # First check if any are local files
        if prefer_local:
            local_entries = [
                (key, data) for key, data in entries if self.is_local_file(data)
            ]
            if local_entries:
                # If multiple local files, prefer the one with more complete metadata
                if len(local_entries) > 1:
                    return self._select_most_complete(local_entries)
                return local_entries[0]

        # No local files or not preferring them, select entry with most complete metadata
        return self._select_most_complete(entries)

    def _select_most_complete(self, entries):
        """
        Select the entry with the most complete metadata.

        Args:
            entries: List of (key, data) tuples

        Returns:
            tuple: (best_key, best_data)
        """
        best_key, best_data = None, None
        best_score = -1

        for key, data in entries:
            score = 0

            # Score based on presence of metadata fields
            for field in [
                "track_name",
                "artist_name",
                "album_name",
                "thumbnail_url",
                "duration",
            ]:
                if field in data and data[field]:
                    score += 1

            # Bonus for URLs
            if "url" in data and data["url"]:
                if self.is_local_file(data):
                    score += 3  # Bigger bonus for local files
                else:
                    score += 1

            # Prefer shorter, cleaner keys
            if not best_key or score > best_score:
                best_key, best_data = key, data
                best_score = score

        return best_key, best_data

    # Additional helper methods for Aurras integration

    def get_best_song_url(self, song_name, song_dict):
        """
        Find the best URL for a song name from the song dictionary.

        Args:
            song_name: Name of the song to find
            song_dict: Dictionary of songs

        Returns:
            str: Best URL (local file path or YouTube URL)
        """
        # First try exact match
        if song_name in song_dict and "url" in song_dict[song_name]:
            return song_dict[song_name]["url"]

        # Try fuzzy match
        best_match, best_score = None, 0

        for key, data in song_dict.items():
            # Match by key
            key_score = self.similarity(song_name, key)

            # Also match by track_name field
            track_score = 0
            if "track_name" in data and data["track_name"]:
                track_score = self.similarity(song_name, data["track_name"])

            score = max(key_score, track_score)

            if score > best_score and score >= self.threshold:
                best_score = score
                best_match = key

        if best_match and "url" in song_dict[best_match]:
            return song_dict[best_match]["url"]

        return None
