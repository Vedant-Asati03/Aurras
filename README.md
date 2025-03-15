# 🎵 Aurras Music Player

Aurras is a feature-rich command-line music player that lets you search, play, and manage music from various sources. With support for online streaming and offline playback, playlists, queue management, and more, it's the ultimate terminal-based music companion.

![Aurras Music Player](https://raw.githubusercontent.com/USERNAME/Aurras/main/assets/screenshot.png)

<div align="center">

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.txt)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![MPV](https://img.shields.io/badge/player-mpv-orange)](https://mpv.io/)
[![PyPI version](https://badge.fury.io/py/aurras.svg)](https://badge.fury.io/py/aurras)

</div>

## Table of Contents
- [🎵 Aurras Music Player](#-aurras-music-player)
  - [Table of Contents](#table-of-contents)
  - [✨ Features](#-features)
  - [Requirements](#requirements)
  - [🚀 Installation](#-installation)
    - [Development Installation](#development-installation)
    - [External Dependencies](#external-dependencies)
  - [📖 Usage](#-usage)
    - [Basic Usage](#basic-usage)
    - [Key Commands](#key-commands)
    - [Playback Controls](#playback-controls)
  - [🎬 Demo](#-demo)
  - [Project Structure](#project-structure)
  - [Technical Details](#technical-details)
  - [Development](#development)
    - [Setup Development Environment](#setup-development-environment)
    - [Testing](#testing)
  - [👥 Contributing](#-contributing)
  - [Troubleshooting](#troubleshooting)
  - [📝 License](#-license)

## ✨ Features

- 🎧 **Online & Offline Playback** - Stream songs online or play downloaded tracks
- 📋 **Queue Management** - Create and manage song queues easily
- 📚 **Playlist Support** - Create, import, download, and manage playlists
- 📥 **Download Support** - Download songs for offline listening
- 🎤 **Lyrics Display** - View and translate lyrics while listening
- 📱 **Spotify Integration** - Import your Spotify playlists
- 🧠 **Smart History** - Track and replay your listening history
- ⌨️ **Command Palette** - Quick access to all features

## Requirements

- Python 3.12 or higher
- MPV media player (for audio playback)
- FFmpeg (required for audio processing)
- Internet connection for streaming and downloading music

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/USERNAME/Aurras.git
cd Aurras

# Install dependencies
pip install -r requirements.txt

# Run Aurras
python -m aurras
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

## 📖 Usage

### Basic Usage

Just type a song name to search and play:

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

### Key Commands

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

### Playback Controls

- `q` - End playback
- `b` - Previous song
- `n` - Next song
- `p` - Pause/Resume
- `t` - Translate lyrics
- `UP`/`DOWN` - Adjust volume

## 🎬 Demo

Check out our [YouTube demo](https://youtube.com/watch?v=DEMO_ID) to see Aurras in action!

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

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Troubleshooting

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.