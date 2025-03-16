# Changelog

All notable changes to the Aurras Music Player will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- Advanced music recommendations based on listening history
- Multi-language support

## [1.1.0] - 2024-03-15

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

## [0.1.0] - 2023-07-15

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
