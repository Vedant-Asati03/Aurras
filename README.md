# Aurras Music Player

Aurras is a feature-rich command-line music player that provides a seamless music experience through your terminal. With support for online streaming, offline playback, playlist management, and integration with services like Spotify, Aurras offers a comprehensive music solution without the need for a graphical interface.

![Aurras main interface](/assets/main-interface.png)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.txt)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![MPV](https://img.shields.io/badge/player-mpv-orange)](https://mpv.io/)
[![PyPI version](https://img.shields.io/badge/version-1.1.1-blue)](https://pypi.org/project/aurras/)

## Table of Contents

- [Aurras Music Player](#aurras-music-player)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Features](#features)
  - [Requirements](#requirements)
  - [Installation](#installation)
    - [Quick Install](#quick-install)
    - [Development Installation](#development-installation)
    - [External Dependencies](#external-dependencies)
      - [FFmpeg Installation](#ffmpeg-installation)
      - [MPV Installation](#mpv-installation)
  - [Usage](#usage)
    - [Running Aurras](#running-aurras)
    - [Basic Commands](#basic-commands)
    - [Playback Controls](#playback-controls)
    - [Command Palette](#command-palette)
    - [Playlist Management](#playlist-management)
      - [Basic Playlist Commands](#basic-playlist-commands)
      - [Advanced Playlist Management](#advanced-playlist-management)
      - [Playlist Command Shortcuts](#playlist-command-shortcuts)
    - [Spotify Integration](#spotify-integration)
    - [Offline Listening](#offline-listening)
  - [Advanced Features](#advanced-features)
    - [Intelligent Caching](#intelligent-caching)
    - [Token Authentication](#token-authentication)
  - [Backup and Restore](#backup-and-restore)
  - [Troubleshooting](#troubleshooting)
  - [Project Structure](#project-structure)
  - [Contributing](#contributing)
    - [Getting Started](#getting-started)
    - [Contribution Guidelines](#contribution-guidelines)
    - [Development Setup](#development-setup)
    - [Bug Reports and Feature Requests](#bug-reports-and-feature-requests)
  - [License](#license)

## Overview

Aurras transforms your terminal into a powerful music player with rich features that rival many graphical applications. Search and play music from various sources, manage playlists, display lyrics, and enjoy a streamlined listening experience — all from your command line.

![Aurras playing song](/assets/playing-song.png)

## Features

- **Online Music Playback**: Stream music directly from YouTube
- **Offline Listening**: Download and play music without an internet connection
- **Playlist Management**: Create, edit, and organize playlists
- **Queue Management**: Add multiple songs to a queue for sequential playback
- **Lyrics Display**: View lyrics synchronized with the current song
- **Lyrics Translation**: Translate displayed lyrics with a single keystroke
- **Spotify Integration**: Import your Spotify playlists with secure token-based authentication
- **Command Palette**: Quick access to features and settings
- **Play History Tracking**: Keep track of recently played songs
- **Settings Customization**: Tailor the application to your preferences
- **Backup and Restore**: Protect your playlists and settings with automated backups

## Requirements

- Python 3.12 or higher
- MPV media player (for audio playback)
- FFmpeg (required for audio processing)
- Internet connection for streaming and downloading music
- External tools installed as described below

## Installation

### Quick Install

```bash
pip install aurras
```

### Development Installation

For development or to have the latest features:

```bash
git clone https://github.com/vedant-asati03/Aurras.git
cd Aurras
chmod +x dev_install.sh
./dev_install.sh
```

This installs Aurras in development mode, allowing code changes without reinstallation.

### External Dependencies

#### FFmpeg Installation

```bash
# Debian/Ubuntu
sudo apt install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg

# Fedora
sudo dnf install ffmpeg

# macOS
brew install ffmpeg

# Windows (using Chocolatey)
choco install ffmpeg
```

#### MPV Installation

```bash
# Debian/Ubuntu
sudo apt install mpv

# Arch Linux
sudo pacman -S mpv

# Fedora
sudo dnf install mpv

# macOS
brew install mpv

# Windows (using Chocolatey)
choco install mpv
```

## Usage

### Running Aurras

Aurras offers two interface modes:

1. **CLI Mode (Default)**: The traditional command-line interface

### Basic Commands

Type a song name to search and play:

```
> Shape of You
```

Play multiple songs in sequence by separating them with commas:

```
> Blinding Lights, Save Your Tears, Starboy
```

For songs with commas in their names, use quotes:

```
> "Don't Stop Believin', Journey"
```

Access the command palette with `>` or `cmd`:

```
> cmd
```

### Playback Controls

- `q` - End playback
- `b` - Previous song
- `n` - Next song
- `p` - Pause/Resume
- `t` - Translate lyrics
- `UP`/`DOWN` - Adjust volume

### Command Palette

| Command           | Description                 |
| ----------------- | --------------------------- |
| `help`            | Display help information    |
| `queue`           | Show the current song queue |
| `clear_queue`     | Clear the queue             |
| `history`         | View recently played songs  |
| `previous`        | Play the previous song      |
| `play_offline`    | Browse downloaded songs     |
| `download_song`   | Download songs              |
| `play_playlist`   | Play a playlist             |
| `import_playlist` | Import from Spotify         |
| `toggle_lyrics`   | Turn lyrics on/off          |

### Playlist Management

Aurras provides comprehensive playlist management features:

#### Basic Playlist Commands

| Command             | Description                               |
| ------------------- | ----------------------------------------- |
| `play_playlist`     | Play songs from a playlist                |
| `shuffle_playlist`  | Play a playlist in random order           |
| `view_playlist`     | View the contents of a playlist           |
| `download_playlist` | Download a playlist for offline listening |
| `delete_playlist`   | Delete a playlist                         |
| `import_playlist`   | Import playlists from Spotify             |

#### Advanced Playlist Management

| Command                     | Description                            |
| --------------------------- | -------------------------------------- |
| `add_song_to_playlist`      | Add a new song to an existing playlist |
| `remove_song_from_playlist` | Remove a song from a playlist          |
| `move_song_up`              | Move a song up in the playlist order   |
| `move_song_down`            | Move a song down in the playlist order |

#### Playlist Command Shortcuts

| Shortcut                 | Description                        |
| ------------------------ | ---------------------------------- |
| `pl <playlist_name>`     | View the contents of a playlist    |
| `spl <playlist_name>`    | Play a playlist in shuffle mode    |
| `aps <playlist>, <song>` | Add a song to a playlist           |
| `rps <playlist>, <song>` | Remove a song from a playlist      |
| `pn <playlist_name>`     | Play a saved playlist online       |
| `pf <playlist_name>`     | Play a downloaded playlist offline |

### Spotify Integration

Import your Spotify playlists with secure token-based authentication.

### Offline Listening

Download and play music without an internet connection.

## Advanced Features

### Intelligent Caching

Aurras intelligently caches frequently played songs to reduce load times and data usage.

### Token Authentication

Aurras uses secure OAuth token-based authentication for Spotify and other integrated services. This provides:

- **Revocation Support**: Easily revoke access when needed

For detailed instructions on setting up Spotify authentication, see our [Spotify Integration Guide](/docs/spotify_integration.md).

## Backup and Restore

Aurras offers backup functionality to protect your music library:

- **Automated Backups**: Regular backups of your playlists and settings
- **Manual Backups**: Create backups on demand when needed
- **Full Restoration**: Restore your complete library from any backup point

Backup files are stored in a compressed format in your user directory.

## Troubleshooting

If you encounter issues while using Aurras, please refer to our detailed [troubleshooting guide](/docs/troubleshooting.md) for common problems and their solutions.

Common issues include:
- Audio playback not working
- Missing dependencies 
- Authentication failures with Spotify
- Download errors

The troubleshooting guide provides step-by-step solutions and diagnostic procedures to resolve these and other technical issues.

## Project Structure

```
aurras/
├── core/           # Core functionality and settings
├── player/         # Playback functionality (online and offline)
├── playlist/       # Playlist management
├── services/       # External service integrations
│   ├── spotify/    # Spotify API integration
│   └── youtube/    # YouTube search and streaming
├── ui/             # User interface components
└── utils/          # Utility functions and helpers
```

## Contributing

We welcome contributions to Aurras! Please check out our [CONTRIBUTING.md](CONTRIBUTING.md) file for detailed guidelines on how to contribute to the project.

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a branch** for your feature or bug fix
4. **Make your changes**, adding tests when possible
5. **Run the test suite** to ensure nothing is broken
6. **Submit a pull request** with a clear description of the changes

### Contribution Guidelines

- Follow the existing code style and conventions
- Write clear, documented, and testable code
- Keep pull requests focused on a single feature or bug fix
- Update documentation for any changed functionality

### Development Setup

See the [Development Installation](#development-installation) section for setting up your development environment.

### Bug Reports and Feature Requests

Please use the GitHub issue tracker to report bugs or suggest features.

For more details, see our [full contribution guide](CONTRIBUTING.md).
[](/CONTRIBUTING.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.