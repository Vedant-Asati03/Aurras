# Changelog

All notable changes to the Aurras Music Player will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Advanced music recommendations based on listening history
- Multi-language support
- Text User Interface (TUI) mode with Textual framework
- Disco mode feature
- Discover feature for music exploration

## [2.1.0] - 2025-06-20

### Changed

- Removed authentication dependencies for cleaner architecture
- Added settings validation and key existence checking
- Enhanced OAuth cache management for Spotify integration

## [2.0.0] - 2024-12-15

### Added

- **Major Interface Overhaul**

  - Dual interface system supporting both CLI and TUI modes
  - Beautiful, responsive terminal UI built with Textual
  - Mouse support alongside keyboard shortcuts
  - Real-time display of playback status, queue, history, and metadata

- **Advanced Synced Lyrics System**

  - Real-time synchronized lyrics with millisecond-accurate timing
  - Word-level highlighting with gradient effects
  - Theme-integrated visual effects
  - Multi-format LRC timestamp support
  - Context-aware display with smooth transitions
  - Collapsible lyrics view (toggle with `l` key)

- **Dynamic Intelligence Search**

  - Context-aware search bar with live recommendations
  - Smart autocompletion that improves with usage
  - Command palette integration (type '>')
  - Options menu access (type '?')
  - Adaptive highlighting with theme-aware colors
  - Navigation history with arrow key support
  - Real-time song suggestions as you type

- **Comprehensive Theme System**

  - 10 built-in themes **(Galaxy, Neon, Vintage, Minimal, Nightclub, Cyberpunk, Forest, Ocean, Sunset, Monochrome)**
  - Live theme switching mid-playback (press `t`)
  - Custom theme creation support via `themes.yaml`
  - Complete visual consistency across all components
  - Deep customization for every interface element

- **Advanced Playlist Management**

  - Intelligent playlist creation with auto-setup
  - Fuzzy name matching for playlist search
  - Batch operations on multiple playlists
  - Rich metadata with descriptions and timestamps
  - Database-backed storage with SQLite
  - Smart search engine for playlists
  - Enhanced Spotify import with OAuth authentication
  - Selective import options for specific playlists

- **High-Quality Download System**

  - Multiple format support **(MP3, FLAC, M4A, OGG, OPUS, WAV)**
  - Configurable bitrates **(8k to 320k)**
  - Batch playlist downloads
  - Smart local prioritization for offline playback
  - Intelligent file organization
  - Download status tracking with progress monitoring
  - Gapless integration between online and offline playback

- **Advanced Playback Controls**

  - Jump Mode - press numbers before `b` or `n` to jump multiple songs
  - Real-time feedback during playback
  - Enhanced queue management with multi-song support
  - Improved seek controls with visual feedback

- **Comprehensive Settings & Configuration**

  - Hierarchical settings system with inheritance
  - Customizable keyboard shortcuts
  - Command and shorthand customization
  - Appearance settings with fine-grained control
  - YAML-based configuration at `~/.aurras/config/settings.yaml`

- **Intelligent Backup & Restore System**

  - Automated backup scheduling (configurable intervals)
  - Selective backup items (settings, playlists, history, downloads)
  - Smart backup cleanup with retention policies
  - One-click recovery system
  - Platform-specific storage locations
  - Integrity validation and corruption detection

- **Enhanced Multi-Source Integration**
  - Improved YouTube integration with advanced search filters
  - Enhanced Spotify OAuth with automatic token refresh
  - Unified search engine across all sources
  - Quality preferences and source management

### Changed

- **Complete UI/UX Redesign**

  - Modern terminal interface with rich visual elements
  - Improved command organization and categorization
  - Enhanced user feedback and interaction patterns
  - Better error handling and user guidance

- **Performance Improvements**

  - Optimized database operations
  - Improved search response times
  - Better memory management
  - Enhanced caching mechanisms

- **Enhanced Documentation**
  - Comprehensive README with detailed feature explanations
  - Updated installation and setup guides
  - Detailed troubleshooting documentation
  - Improved keyboard shortcuts reference

### Fixed

- Improved error handling across all modules
- Better network failure recovery
- Enhanced playlist synchronization
- Resolved display update issues during playback
- Fixed song parsing with special characters
- Improved stability for long-running sessions

### Security

- Enhanced OAuth token handling for Spotify integration
- Improved credential storage and management
- Better authentication error handling

## [1.1.1] - 2024-03-15

### Added

- Enhanced Spotify integration
  - Implemented persistent token-based authentication
  - Added automatic token refreshing to avoid repeated logins
  - Improved error handling for authentication failures
  - Enhanced user guidance during authentication process
- Enhanced song parsing to support songs with commas in their titles using quotes
- Improved queue management with multi-song support
- Added `add_to_queue` command to add songs to the queue without playing
- Added cache management features (`cache_info` and `cleanup_cache`)
- More detailed help menu with command categorization
- Comprehensive documentation updates
  - Added Spotify integration guide
  - Added detailed troubleshooting documentation
  - Created keyboard shortcuts reference
  - Updated playlist management guide
- Enhanced playlist management features
  - Playlist song reordering (move up/down)
  - Playlist shuffling
  - Adding/removing songs from existing playlists
  - Improved playlist browsing with formatted tables
- Improved theme consistency with app colors
- New playlist command shortcuts for faster management
- Added proper database directory structure
- Backup and restore functionality for user data

### Changed

- Reorganized help menu with clearer command categories
- Improved user feedback for commands
- Better error handling in song downloads

### Fixed

- Spotify playlist import functionality
- Playlist navigation and playback issues
- Fixed song parsing when commas are present in song titles
- Improved history navigation between songs
- Enhanced playlist handling with better error feedback
- Improved error handling for network failures

## [0.1.1] - 2023-07-15

### Added

- Initial release of Aurras Music Player
- Online song playback from YouTube
- Offline playback of downloaded songs
- Song queue management
- Playlist creation, import, and management
- Spotify integration for importing playlists
- Lyrics display with translation support
- Command-line interface with rich formatting
- Command palette for quick access to features
- Play history tracking and navigation
- Settings customization
