# Search Implementation Documentation

This document provides a comprehensive overview of Aurras' sophisticated search module architecture, explaining how the multi-provider system works to deliver seamless music discovery across different sources.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Search Flow](#search-flow)
- [Provider System](#provider-system)
- [Fuzzy Search Engine](#fuzzy-search-engine)
- [Cache Management](#cache-management)
- [Integration Points](#integration-points)
- [Performance Optimizations](#performance-optimizations)
- [Code Examples](#code-examples)

## Architecture Overview

Aurras implements a **layered, provider-based search architecture** that seamlessly integrates multiple music sources while providing intelligent caching and fuzzy matching capabilities. The system is designed around the principle of **separation of concerns**, where different components handle specific aspects of the search process.

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│                 (TUI Commands, CLI)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Search Coordinator                           │
│                  (SongSearch)                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
            ┌─────────┴─────────┐
            │                   │
┌───────────▼──────────┐ ┌──────▼──────────────────┐
│   Cache Provider     │ │ Search Provider         │
│(DatabaseCacheProvider) │(YouTubeSearchProvider)  │
└───────────┬──────────┘ └──────┬──────────────────┘
            │                   │
┌───────────▼──────────┐ ┌──────▼──────────┐
│   Fuzzy Search       │ │   YTMusic API   │
│     Engine           │ │   Integration   │
└──────────────────────┘ └─────────────────┘
```

## Core Components

### 1. SongSearch (Main Coordinator)

**Location**: `aurras/services/youtube/search.py`

The `SongSearch` class serves as the central coordinator that orchestrates the entire search process. It manages the interaction between different providers and handles the combination of history and search results.

**Key Responsibilities**:
- Coordinating searches across multiple providers
- Managing search history integration
- Handling provider fallbacks
- Maintaining queue start index for seamless playback

**Interface**:
```python
class SongSearch:
    def search(
        self,
        queries: List[str] | str,
        include_history: bool = True,
        history_limit: int = 30,
    ) -> List[SongResult]
```

### 2. Provider System

The search system uses a **provider pattern** to support multiple music sources while maintaining a consistent interface.

#### SearchProvider Protocol
```python
class SearchProvider(Protocol):
    def search(self, queries: List[str]) -> List[SongResult]:
        """Search for songs."""
        ...
```

#### CacheProvider Protocol
```python
class CacheProvider(Protocol):
    def get_songs(self, queries: List[str]) -> Dict[str, SongResult]:
        """Get songs from cache."""
        ...
    
    def save_songs(self, query_to_song: Dict[str, SongResult]) -> None:
        """Save songs to cache."""
        ...
    
    def get_recent_songs(self, limit: int = 30) -> List[SongResult]:
        """Get recently played songs."""
        ...
```

### 3. SongResult Data Structure

The `SongResult` is a `NamedTuple` that standardizes song information across all providers:

```python
class SongResult(NamedTuple):
    name: str                    # Song title
    url: str                     # Playback URL
    thumbnail_url: str = ""      # Album artwork URL
    artist: str = ""             # Artist name
    album: str = ""              # Album name
    is_from_history: bool = False # History flag
```

## Search Flow

The search process follows a **multi-stage workflow** that prioritizes cached results and falls back to online searches when necessary:

### Stage 1: History Integration (Optional)
```
User Query → History Check → Recent Songs Retrieval
```

### Stage 2: Cache Lookup
```
Search Queries → Database Cache → Fuzzy Matching → Cached Results
```

### Stage 3: Online Search (Fallback)
```
Uncached Queries → YouTube API → Song Metadata Extraction → Cache Update
```

### Stage 4: Result Combination
```
History + Cached + Online Results → Queue Assembly → Playback Ready
```

## Provider System

### YouTubeSearchProvider

**Location**: `aurras/services/youtube/search.py:60`

Handles direct interaction with the YouTube Music API using the `ytmusicapi` library.

**Features**:
- **Single Query Processing**: Searches for individual songs with metadata extraction
- **Temporary Storage**: Caches results within session to avoid redundant API calls
- **Rich Metadata**: Extracts title, artist, album, thumbnail, and video ID
- **Error Handling**: Graceful degradation when API calls fail

**Search Process**:
1. Check temporary storage for cached results
2. Execute YTMusic API search with song filter
3. Extract comprehensive metadata from response
4. Construct YouTube URL from video ID
5. Create and return `SongResult` object

### DatabaseCacheProvider

**Location**: `aurras/services/youtube/search.py:130`

Manages the sophisticated caching system that combines multiple data sources.

**Data Sources**:
- **Search History Database**: Previously searched songs with metadata
- **Downloads Database**: Locally downloaded music files
- **Playback History**: Recently played songs for queue integration

**Key Features**:
- **Database Merging**: Intelligently combines cache and downloads databases
- **Fuzzy Matching**: Uses advanced fuzzy search for query correction
- **Metadata Enrichment**: Merges metadata from multiple sources
- **History Integration**: Seamlessly integrates recent playback history

## Fuzzy Search Engine

### FuzzySearcher Class

**Location**: `aurras/utils/handle_fuzzy_search.py:10`

The core fuzzy search implementation optimized for music searches.

**Features**:
- **Music-Specific Optimizations**: Handles common music patterns and formats
- **Configurable Thresholds**: Adjustable similarity scoring
- **Caching**: LRU cache for performance optimization
- **Thread Safety**: Safe for concurrent use

**Key Methods**:
```python
def similarity(self, query: str, track_name: str) -> float:
    """Calculate similarity score between query and track name."""

def search_songs(self, query: str, song_data: dict, metadata_keys: dict) -> list:
    """Specialized search for song dictionaries with metadata support."""

def find_best_match(self, query: str, track_names: List[str]) -> Optional[str]:
    """Find the best matching track name for a query."""
```

### FuzzyDictMatcher Class

**Location**: `aurras/utils/handle_fuzzy_search.py:334`

Advanced dictionary-based matching system designed specifically for music metadata.

**Music-Specific Processing**:
- **Pattern Normalization**: Removes common video suffixes and formatting
- **Featured Artist Handling**: Standardizes "feat." and "ft." patterns
- **Metadata Field Mapping**: Maps various metadata field names to standard formats
- **Database Merging**: Intelligently combines multiple song databases

**Text Cleaning Patterns**:
```python
# Video-specific patterns
(re.compile(r"\(official\s+video\)", re.IGNORECASE), "")
(re.compile(r"\(official\s+audio\)", re.IGNORECASE), "")
(re.compile(r"\(lyrics\)", re.IGNORECASE), "")

# Featured artist patterns
(re.compile(r"\(feat\..*?\)", re.IGNORECASE), "")
(re.compile(r"\(ft\..*?\)", re.IGNORECASE), "")
```

## Cache Management

### Multi-Level Caching Strategy

Aurras implements a sophisticated **three-tier caching system**:

#### 1. Session Cache (Temporary Storage)
- **Scope**: Current search session
- **Purpose**: Avoid redundant API calls within session
- **Implementation**: In-memory dictionary in providers
- **Persistence**: Memory only (cleared on restart)

#### 2. Database Cache (Persistent)
- **Scope**: All historical searches
- **Purpose**: Long-term query optimization
- **Implementation**: SQLite database with rich metadata
- **Persistence**: Permanent storage with metadata

#### 3. Downloads Cache (Local Files)
- **Scope**: Downloaded music library
- **Purpose**: Prioritize local content
- **Implementation**: File system integration with metadata
- **Persistence**: Permanent with file metadata

### Cache Update Strategy

```python
# Smart cache updating process
def save_songs(self, query_to_song: Dict[str, SongResult]) -> None:
    """Save songs with complete metadata to the database cache."""
    
    # 1. Check for existing entries to avoid duplicates
    existing_songs = self.search_db.initialize_full_song_dict()
    
    # 2. Duplicate detection by URL and metadata
    for query, song in query_to_song.items():
        exists = self._check_song_exists(song, existing_songs)
        
        # 3. Save only new songs with enhanced metadata
        if not exists:
            self.updater.save_to_cache(
                song_user_searched=query,
                track_name=song.name,
                url=song.url,
                artist_name=song.artist,
                album_name=song.album,
                thumbnail_url=song.thumbnail_url,
                duration=0,
            )
```

## Integration Points

### TUI Command Integration

**Location**: `aurras/tui/commands/song_search.py`

The search system integrates with the TUI through the `SongSearchProvider` class, which provides real-time search suggestions and command completion.

**Features**:
- **Asynchronous Search**: Non-blocking search operations
- **History Integration**: Shows previously searched songs
- **Smart Suggestions**: Provides remix, acoustic, and live variants
- **Real-time Results**: Streams results as they're found

### Player Integration

**Location**: `aurras/core/player/mpv/history_integration.py`

The search results seamlessly integrate with the media player through the history integration system.

**Integration Process**:
1. **Queue Assembly**: Combines history and search results
2. **Index Management**: Tracks starting position for new searches
3. **Seamless Playback**: Enables continuous playback across sources
4. **History Updates**: Records playback for future search enhancement

### Playlist Integration

**Location**: `aurras/core/playlist/cache/search_db.py`

Search results can be directly added to playlists through the playlist management system.

## Performance Optimizations

### 1. Intelligent Caching
- **LRU Cache**: Frequently accessed normalization and similarity calculations
- **Database Indexing**: Optimized database queries for fast lookups
- **Batch Processing**: Efficient handling of multiple queries

### 2. Lazy Loading
- **On-Demand Search**: YouTube API calls only when cache misses
- **Progressive Results**: Stream results as they become available
- **Background Updates**: Cache updates don't block user interface

### 3. Fuzzy Matching Optimizations
- **Compiled Patterns**: Pre-compiled regex for fast text processing
- **Threshold Tuning**: Optimized similarity thresholds for music content
- **Short-Circuit Evaluation**: Early termination for obvious non-matches

### 4. Thread Safety
- **Concurrent Searches**: Thread-safe fuzzy search instances
- **Database Connections**: Managed connection pooling
- **Lock-Free Operations**: Minimized blocking operations

## Code Examples

### Basic Search Usage

```python
# Initialize search coordinator
search = SongSearch()

# Simple search
results = search.search("bohemian rhapsody")

# Search with history integration
results = search.search(
    ["song1", "song2"], 
    include_history=True, 
    history_limit=20
)

# Get playback information
combined_results, start_index = search.get_playback_info()
```

### Custom Provider Implementation

```python
class SpotifySearchProvider:
    """Example custom search provider."""
    
    def search(self, queries: List[str]) -> List[SongResult]:
        results = []
        for query in queries:
            # Custom Spotify search logic
            spotify_result = self.spotify_search(query)
            
            result = SongResult(
                name=spotify_result.title,
                url=spotify_result.uri,
                artist=spotify_result.artist,
                album=spotify_result.album,
                thumbnail_url=spotify_result.artwork
            )
            results.append(result)
        
        return results

# Use custom provider
custom_search = SongSearch(search_provider=SpotifySearchProvider())
```

### Advanced Fuzzy Search

```python
# Initialize fuzzy searcher with custom settings
fuzzy = FuzzySearcher(
    threshold=0.7,
    use_cache=True,
    music_mode=True
)

# Search with metadata weights
metadata_keys = {
    "track_name": 1.0,    # Full weight for song title
    "artist_name": 0.8,   # High weight for artist
    "album_name": 0.6     # Medium weight for album
}

results = fuzzy.search_songs(
    query="bohemian rhapsody",
    song_data=song_database,
    metadata_keys=metadata_keys
)
```

### Cache Management

```python
# Initialize cache provider
cache = DatabaseCacheProvider()

# Get cached songs
cached_results = cache.get_songs(["query1", "query2"])

# Save new results to cache
query_to_song = {
    "bohemian rhapsody": SongResult(
        name="Bohemian Rhapsody",
        url="https://youtube.com/watch?v=...",
        artist="Queen",
        album="A Night at the Opera"
    )
}
cache.save_songs(query_to_song)

# Get recent history
recent_songs = cache.get_recent_songs(limit=30)
```

---

## Summary

The Aurras search implementation represents a sophisticated, multi-layered architecture that provides:

- **Unified Interface**: Consistent API across multiple music sources
- **Intelligent Caching**: Multi-tier caching for optimal performance
- **Fuzzy Matching**: Music-optimized search algorithms
- **Seamless Integration**: Deep integration with player and playlist systems
- **Extensible Design**: Provider pattern for easy source addition

This architecture ensures that users get fast, relevant search results while maintaining the flexibility to add new music sources and optimize performance based on usage patterns.
