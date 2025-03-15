# Changelog

All notable changes to the Aurras Music Player will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- Advanced music recommendations based on listening history
- Multi-language support

## [1.1.0] - 2023-12-15

### Added
- Enhanced song parsing to support songs with commas in their titles using quotes
- Improved queue management with multi-song support
- Added `add_to_queue` command to add songs to the queue without playing
- Added cache management features (`cache_info` and `cleanup_cache`)
- More detailed help menu with command categorization
- Comprehensive documentation (README, CHANGELOG, CONTRIBUTING)

### Changed
- Reorganized help menu with clearer command categories
- Improved user feedback for commands
- Better error handling in song downloads

### Fixed
- Fixed song parsing when commas are present in song titles
- Improved history navigation between songs
- Enhanced playlist handling with better error feedback

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
