# Aurras Music Player

![Aurras](assests/aurras.png)

**Aurras🎧** is a high-end **command line music player** that offers a seamless music experience directly in your terminal. It combines powerful search capabilities with an elegant interface, allowing you to enjoy your favorite music without leaving your command line environment.

<div align="center">

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.txt)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![MPV](https://img.shields.io/badge/player-mpv-orange)](https://mpv.io/)
[![PyPI version](https://badge.fury.io/py/aurras.svg)](https://badge.fury.io/py/aurras)

</div>

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Standard Installation](#standard-installation)
  - [Development Installation](#development-installation)
- [Usage Guide](#usage-guide)
  - [Command Line Arguments](#command-line-arguments)
  - [Interactive Mode](#interactive-mode)
  - [Command Shortcuts](#command-shortcuts)
  - [Playlist Management](#playlist-management)
  - [Spotify Integration](#spotify-integration)
- [Project Structure](#project-structure)
- [Technical Details](#technical-details)
- [Development](#development)
  - [Setup Development Environment](#setup-development-environment)
  - [Testing](#testing)
  - [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

* **Online Streaming** - Play any song directly without downloading
* **Offline Playback** - Listen to your downloaded songs locally
* **Smart Caching** - Searches local cache before making web requests for better performance
* **Playlist Management** - Create, import, download and manage playlists
* **Spotify Integration** - Import your Spotify playlists directly
* **Command Shortcuts** - Quickly perform actions with intuitive shortcuts
* **Lyrics Display** - View song lyrics while playing
* **Auto-completion** - Smart song and playlist name suggestions
* **Song Recommendations** - Get personalized song recommendations
* **Backup & Restore** - Automatic backup of your preferences and playlists
* **Flexible Configuration** - Customize settings through YAML configuration files

## Requirements

- Python 3.12 or higher
- MPV media player (for audio playback)
- FFmpeg (required for audio processing)
- Internet connection for streaming and downloading music

## Installation

### Standard Installation

The easiest way to install Aurras is via pip:

```bash
pip install aurras
```

### Development Installation

For development or to have the latest features, install from source:

1. Clone the repository:
```bash
git clone https://github.com/vedant-asati03/Aurras.git
cd Aurras
```

2. Run the development installation script:
```bash
chmod +x dev_install.sh
./dev_install.sh
```

This will install Aurras in development mode, allowing you to make changes to the code without having to reinstall the package each time.

### External Dependencies

1. Install FFmpeg (required for audio playback):
```bash
# Debian/Ubuntu
sudo apt install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg

# Fedora
sudo dnf install ffmpeg

# Windows (using Chocolatey)
choco install ffmpeg

# macOS (using Homebrew)
brew install ffmpeg
```

2. Install MPV player:
```bash
# Debian/Ubuntu
sudo apt install mpv

# Arch Linux
sudo pacman -S mpv

# Fedora
sudo dnf install mpv

# Windows (using Chocolatey)
choco install mpv

# macOS (using Homebrew)
brew install mpv
```

## Usage Guide

### Command Line Arguments

Aurras supports various command-line arguments for quick operations:

### Interactive Mode

### Command Shortcuts

Aurras offers convenient shortcuts to quickly perform common actions:

* `d, song1, song2, ...` - Download multiple songs
* `dp, playlist_name` - Download a specific playlist
* `pn, playlist_name` - Play a saved playlist online
* `pf, playlist_name` - Play a downloaded playlist offline
* `rs, playlist_name` - Remove a saved playlist
* `rd, playlist_name` - Remove a downloaded playlist

### Playlist Management

### Spotify Integration

Aurras can connect to your Spotify account to import playlists. When first using Spotify features, you'll be prompted to authenticate and provide your API credentials.

1. Create a Spotify Developer account: https://developer.spotify.com/dashboard/
2. Create an application to obtain your client ID and secret
3. Set the redirect URI to `http://localhost:8888/callback`
4. Enter these credentials when prompted by Aurras

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

## Technical Details

## Development

### Setup Development Environment

### Testing

### Contributing

## Troubleshooting

## License

MIT License - See LICENSE.txt for details