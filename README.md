![Aurras hero image](/assets/aurras.png)

Elevate your music experience. Aurras transforms your terminal into a sophisticated, feature-rich music hub, letting your audio fill your space, uninterrupted and unburdened. **Seamlessly access both online streaming platforms and your local offline music library. Take command with robust playlist management and advanced queue controls for precise playback. Personalize your setup further with deep customizability and vibrant theme support, among many other powerful capabilities.**

[![License](https://img.shields.io/badge/License-MIT-ff6b6b?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE.txt)
[![Python](https://img.shields.io/badge/Python-3.12+-4285f4?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![MPV](https://img.shields.io/badge/Player-MPV-ff8c42?style=for-the-badge&logo=mpv&logoColor=white)](https://mpv.io/)
[![PyPI](https://img.shields.io/badge/PyPI-1.1.1-34a853?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/aurras/)
[![Downloads](https://img.shields.io/badge/Downloads-1K+-00d084?style=for-the-badge&logo=download&logoColor=white)](https://pypi.org/project/aurras/)
[![Discord](https://img.shields.io/badge/Discord-Join_Chat-5865f2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/QDJqZneMVB)
[![Issues](https://img.shields.io/github/issues/vedant-asati03/Aurras?style=for-the-badge&logo=github&logoColor=white&color=ea4a5a)](https://github.com/vedant-asati03/Aurras/issues)
[![Forks](https://img.shields.io/github/forks/vedant-asati03/Aurras?style=for-the-badge&logo=github&logoColor=white&color=9333ea)](https://github.com/vedant-asati03/Aurras/network/members)
[![Stars](https://img.shields.io/github/stars/vedant-asati03/Aurras?style=for-the-badge&logo=github&logoColor=white&color=f59e0b)](https://github.com/vedant-asati03/Aurras)

## Table of Contents

- [Why AURRAS?](#why-choose-aurras)
- [Core Features](#core-features)
- [Installation Guide](#installation-guide-for-aurras)
  - [Development](#clone-and-setup)
- [Service Setup & Integration](#service-setup--integration)
  - [Spotify Integration](#spotify-integration)
- [Customization & Management](#customization-settings--backup-management)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

# Why Choose Aurras?

- **Real-Time Synced Lyrics** - Enjoy advanced lyrics synchronization with gradient highlighting, theme integration, and millisecond-accurate timing that makes every word dance with your music

- **Dynamic Intelligence Search** - Context-aware search bar with live recommendations, smart autocompletion, command palette integration, history integration, all this with adaptive highlighting  

- **Live Theme Ecosystem** - 10 built-in themes with instant switching mid-playback, complete visual consistency across all components, and deep customization for every interface element

- **Comprehensive Settings Engine** - Hierarchical configuration system with highly customizable options, keyboard shortcut remapping, appearance controls, and settings that adapt to your workflow

- **Smart Backup** - Intelligent automated protection with smart restoration, missing media detection, and one-command recovery for complete peace of mind

- **Dual Interface Mastery** - Seamlessly switch between streamlined CLI for power users and feature-rich TUI(Upcoming...) for immersive experiences, both with full feature parity

- **Seamless Platform Integration** - Complete Spotify library import, YouTube unlimited access, local music prioritization, and unified search across all sources with intelligent content discovery

- **Smart Download Management** - High-quality offline music with format selection, instant local playback prioritization, playlist batch downloads, and gapless transitions  

# Core Features

<details>
<summary><b>1. Dual Interface System</b></summary>

Aurras offers both command-line and terminal UI modes to suit different workflows:

## Command-Line Interface (CLI)

- Instant music control with simple commands
- Comes with command-line and interactive mode  
- Lightweight for resource-constrained environments

## Text User Interface (TUI)

- Beautiful, responsive terminal UI built with Textual
- Real-time display of playback status, queue, history, and metadata
- Mouse support alongside keyboard shortcuts

![TUI Interface Demo - Coming Soon](/assets/placeholder-tui-demo.png)

</details>

<details open>
<summary><b>2. Meticulous Playback Control</b></summary>

**"With great power comes great responsibility"** - Aurras understands this very well and that's why it equips you with every weapon in its arsenal that you'll need.

Basic controls are visible at the bottom of the player, but those are not enough, right? Yes, that's what I thought too, which is why it has:

**Jump Mode** - Before pressing `b` or `n`, you can press any *number* to jump through that many songs

**Collapsible Lyrics View** - If you do not want to see the lyrics, you can hide them by pressing `l`

And just to help you with all this, Aurras also provides real-time feedback during playback so you are always in control.
![Aurras playing song](/assets/playing-song.png)

</details>

<details>
<summary><b>3. Dynamic Search & Command System</b></summary>

Oh boy! Where do I even start with this one? A real-time, context-aware search bar featuring command palette, options menu, and even supports shortcuts for commands and shorthands!

But wait, there's more! Every keystroke is intelligently highlighted with **adaptive theming** that matches your current theme, making commands and search terms visually distinct. As you type, Aurras provides **live song recommendations** right in the search bar, and maintains a **smart history** accessible with simple up/down arrow keys.

**Intelligent Search Features**:

**Smart Autocompletion** - Not just basic autocomplete, the more you use it the better it gets

**Contextual Highlighting** - Commands, song names, and search operators are beautifully highlighted with theme-aware colors

**Instant Recommendations** - See song suggestions appear in real-time as you type, no need to hit enter

**Navigation History** - Use `↑` and `↓` arrows to browse through your search history like a true terminal pro

*For a detailed look at how the intelligent search bar functions, a dedicated blog post is currently in the works.*

<!-- If you are intrigued like me, you can check out how the search bar works under the hood, here  -->

<details open>
<summary><b>Command Palette (Type >)</b></summary>

- **Quick Actions**: Access almost any feature with keyboard shortcuts
- **Easy Run**: View and run the commands directly from command palette

</details>

<details open>
<summary><b>Options Menu (Type ?)</b></summary>

- **Feature Access**: Your only stop to access some the most exclusive app features like streaming your local groove, disco mode (upcoming), discover (upcoming)

</details>

</details>

<details>
<summary><b>4. Advanced Multi-Source Integration</b></summary>

An intelligent Search module is another great feat of aurras, it uses providers to achieve a multi-level search implementation, check the [Search implementation](./docs/search_implementation.md) for better understanding on how it works.

## Unified Search Engine

- **YouTube Integration**: Access millions of songs with advanced search filters
- **Spotify Integration**: Full library access with OAuth authentication
- **Local Music Library**: Download your favourite songs to listen them anytime you want

<details open>
<summary><b>Source Management</b></summary>

- **Present Source**: Currently there is only one source that is youtube, I might consider adding other sources in the future
- **Quality Preferences**: Choose audio quality

</details>
</details>

<details open>
<summary><b>5. High-Quality Music Downloads</b></summary>

Download and manage offline music with support for selecting your preffered format, bitrate, and location.

![Download Example](/assets/download-example-1.png)

You can also download songs as a playlist,

![Download Example as a playlist](/assets/download-example-2.png)

## Offline Integration

- **Prioritized Local Playback**: When you search for a song, Aurras intelligently prioritizes your downloaded version, instantly playing it offline instead of streaming.
- **Instant & Gapless Playback**: Enjoy your downloaded music with truly instant loading times and seamless, gapless transitions between tracks.

</details>

<details>
<summary><b>6. Sophisticated Playlist Management</b></summary>

Master your music collection with Aurras' **intelligent playlist ecosystem** that seamlessly bridges online and offline worlds. Our advanced playlist engine delivers sophisticated management capabilities with smart organization, automated synchronization, and reliability that keeps your musical universe perfectly curated.

**Core Capabilities:** Smart creation • Batch operations • Spotify import • Fuzzy search • Download management • Song manipulation • Queue integration • Database optimization • Sync automation

<details open>
<summary><b>Intelligent Playlist Creation & Management</b></summary>

**Build your musical universe with precision and ease.** Aurras' playlist management system combines intelligent automation with granular control, allowing you to create, organize, and maintain complex playlist hierarchies with database-backed reliability and intelligent search capabilities.

- **Smart Auto-Creation**: Playlists are intelligently created when you first add songs, eliminating the need for manual setup and streamlining your workflow
- **Fuzzy Name Matching**: Advanced fuzzy search corrects typos and variations in playlist names automatically, so `"My Favrites"` finds `"My Favorites"` seamlessly
- **Batch Operations**: Perform bulk operations on multiple playlists simultaneously — create, delete, download, or import with single commands for efficient management
- **Metadata Intelligence**: Rich playlist metadata with descriptions, creation timestamps, update tracking, and download status for comprehensive organization
- **Database-Backed Storage**: SQLite database ensures data integrity, fast retrieval, and reliable persistence across sessions
- **Smart Search Engine**: Search playlists by song names, artist names, or playlist metadata with intelligent ranking and real-time suggestions

*Listen with ease: `aurras playlist my_playlist` — comes with offline playback priority*

</details>

<details open>
<summary><b>Advanced Spotify Integration & Import</b></summary>

**Seamlessly bridge your Spotify universe with Aurras.** Our sophisticated import system provides OAuth-authenticated access to your entire Spotify library with intelligent synchronization, selective import options, and an upcoming feature ~ automated playlist updating that keeps your collections perfectly aligned.

- **OAuth Authentication**: Secure, token-based authentication with automatic refresh ensures persistent access without repeated logins or credential exposure
- **Complete Library Access**: Import entire Spotify library or select specific playlists with full metadata preservation including track names, artists, albums, and playlist descriptions  
- **Intelligent Synchronization**: Smart sync engine detects changes in your Spotify playlists and automatically updates local copies while preserving your customizations
- **Metadata Preservation**: Complete preservation of playlist structure, song order, descriptions, and creation dates for seamless migration experience

*Bridge platforms effortlessly: `aurras playlist --import` — instant access to your entire Spotify collection*

</details>

<details open>
<summary><b>High-Performance Download & Offline Management</b></summary>

**Transform streaming playlists into high-quality offline collections.** Our advanced download engine provides intelligent batch processing, format selection, and local prioritization that ensures your favorite playlists are always available, optimized, and ready for instant playback.

- **Batch Download Intelligence**: Download entire playlists with configurable quality settings, format preferences, and intelligent file organization for optimal storage management
- **Format & Quality Control**: Choose from multiple audio formats (MP3, FLAC, M4A, OGG, OPUS, WAV) with selectable bitrates (8k to 320k) for perfect balance between quality and storage
- **Smart Local Prioritization**: Downloaded songs automatically take priority during playback, providing instant loading and eliminating streaming delays for your collection
- **Intelligent File Organization**: Automatic directory structure creation with playlist-based organization and duplicate detection for clean, manageable music libraries
- **Download Status Tracking**: Real-time progress tracking, error handling ensure reliable downloads even with unstable connections
- **Gapless Integration**: Seamless transition between online streaming and offline playback with intelligent queue management and buffer optimization

*Download with precision: `aurras download --playlist "Chill Mix" --format flac --bitrate 320k`*

</details>

Run `aurras playlist --help` to explore the complete playlist management suite.

</details>

<details>
<summary><b>7. Comprehensive Settings & Configuration</b></summary>

Aurras believes in **"Your music, your way"** — and that philosophy extends deep into every configurable aspect of the application. To start, just run ```aurras settings --help```

Aurras uses `settings.yaml` file to store all your settings located at `~/.aurras/config/settings.yaml`

**Hierarchical Settings** - Settings are organized in logical groups with inheritance, so changing them is very easy `aurras settings --set <key> <value>`

![Updating Settings example](/assets/settings-example-1.png)

## Some Important Settings

<details>
<summary><b>Keyboard Shortcuts</b></summary>

- `quit-playback` **q**
- `toggle-play-pause`  **SPACE**
- `next-track`  **n**
- `previous-track`  **b**
- `volume-up`  **UP**
- `volume-down`  **DOWN**
- `seek-forward`  **RIGHT**
- `seek-backward`  **LEFT**
- `toggle-lyrics`  **l**
- `quit-playback`  **q**
- `stop-jump-mode`  **ESC**
- `switch-themes`  **t**

</details>

<details>
<summary><b>Command and Shorthands</b></summary>

### Commands

- `download-song` **download**
- `play-offline` **offline**
- `play-playlist` **playlist**
- `download-playlist` **downloadp**
- `view-playlist` **view**
- `delete-playlist` **delete**
- `import-playlist` **import**
- `search-by-song-or-artist` **search**
- `display-history` **history**
- `play-previous-song` **previous**
- `clear-listening-history` **clear**
- `setup-spotify` **setup**
- `display-cache-info` **cache**
- `cleanup-cache` **cleanup**
- `toggle-lyrics` **lyrics**
- `self-management` **self** (update, uninstall, version info, check dependencies)

### Shorthands

- `download-song` **d**
- `play-offline` **o**
- `play-previous-song` **prev**
- `play-playlist` **p**
- `download-playlist` **dp**
- `view-playlist` **v**
- `delete-playlist` **de**
- `display-history` **h**

</details>

<details>
<summary><b>Appearance Settings</b></summary>

- `theme` **cyberpunk**
- `display-video` **no**
- `display-lyrics` **no**
- `user-feedback-visible` **yes**
- `date-format` **yyyy-mm-dd**
- `time-format` **24h**

</details>
</details>

<details>
<summary><b>8. Highly Customizable UI & Theming</b></summary>

Aurras ships with a carefully curated collection of themes and design to improve experience and accessibility. To get started quickly run ```aurras theme --help```:

<details open>
<summary><b>Aurras's Theme Collection</b></summary>

- `Galaxy` Deep space-inspired theme with rich purples and blues
- `Neon` Vibrant digital visualization style
- `Vintage` Warm retro vinyl player feel
- `Minimal` Clean distraction-free interface
- `Nightclub` Clean distraction-free interface
- `Cyberpunk` Bright futuristic cyberpunk aesthetic
- `Forest` Earthy green natural environment
- `Ocean` Calming blue oceanic color palette
- `Sunset` Warm orange and pink sunset tones
- `Monochrome` Classic black and white styling

</details>

### Shape Your Listening Space: Interface Customization at Your Fingertips

Aurras provides unparalleled control over its appearance, allowing you to perfectly match your preferences:

- **Live Theme Switching**: Change your player's entire look mid-stream! Just hit `t` to cycle through a variety of themes instantly.
- **Flexible Layouts**: Keep your focus pure or immerse yourself with lyrics. Easily toggle the Lyrics display on/off by pressing `l`.
- **Interactive Feedback**: Decide whether you want to see real-time interaction feedback, ensuring the most streamlined experience for you.

![display of Themes](/assets/theme-display.png)

*If you are interested in knowing how this app centralized theme system works, take a look at [Theme Module](/docs/theme_implementation.md)*
</details>

<details>
<summary><b>9. Advanced Backup & Restore System</b></summary>

Your musical journey is precious, and losing it should never be an option. Aurras delivers **backup protection** with intelligent automation, smart restoration, and comprehensive data preservation that ensures your playlists, preferences, and entire music experience remain safe, accessible, and perfectly restored whenever you need them.

**Core Capabilities:** Automated backups • Smart restoration • Selective backup items • Timed scheduling • Intelligent cleanup • Missing media detection • One-click recovery • Storage optimization • Data integrity

<details open>
<summary><b>️Intelligent Automated Protection</b></summary>

**Never lose a beat with proactive backup automation.** Our intelligent backup system continuously monitors your data and automatically creates comprehensive backups based on configurable schedules, ensuring your musical universe is always protected without manual intervention.

- **Timed Backup Scheduling**: Automatic backups every 24 hours (configurable) with intelligent timing that avoids disrupting your listening sessions
- **Selective Item Backup**: Granular control over what gets backed up — settings, playlists, history, downloads, cache, and credentials with individual enable/disable options
- **Smart Backup Cleanup**: Automatic removal of old backups with configurable retention (default: 10 backups) to prevent storage bloat while maintaining sufficient history
- **Background Processing**: Non-intrusive backup creation that runs silently in the background without affecting playback or system performance
- **Platform-Specific Storage**: Intelligent backup location selection using OS-appropriate directories (Linux: `~/.local/share/aurras/backup`, macOS: `~/Library/Application Support/aurras/backup`, Windows: `%LOCALAPPDATA%\aurras\backup`)
- **Integrity Validation**: Automatic backup verification with metadata tracking and corruption detection for reliable restoration

</details>

Run ```aurras backup --help``` to get started with using backup system.

</details>

<details open>
<summary><b>10. Synced Lyrics Support</b></summary>

Transform your listening experience into an immersive journey where every word comes alive. Aurras delivers **industry-leading synced lyrics** with real-time highlighting, intelligent parsing, and theme-integrated visual effects that make you feel every beat and word as they flow through your speakers.

**Core Capabilities:** Real-time synchronization • Word-level highlighting • Theme integration • Multi-format support • Intelligent caching • Asynchronous fetching • Visual gradients • Context-aware display • Fallback mechanisms • Live positioning

<details open>
<summary><b>Real-Time Synchronized Display</b></summary>

**Experience lyrics that dance with your music.** Our advanced synchronization engine delivers almost pixel-perfect timing with gradient-highlighted text that flows seamlessly with the rhythm, creating an immersive karaoke-like experience right in your terminal.

- **Precision Timing**: Millisecond-accurate synchronization with support for `[mm:ss.ss]` LRC timestamp formats and enhanced word-level timing
- **Live Word Highlighting**: Dynamic gradient effects that highlight the current lyric line with theme-aware colors that adapt to your chosen visual style
- **Context-Aware Display**: Smart context lines that show upcoming and previous lyrics while keeping the current line prominently featured
- **Smooth Transitions**: Fluid text transitions with gradient fading effects that create natural reading flow without jarring jumps
- **Position Tracking**: Real-time playback position integration that instantly updates lyrics display as you seek through tracks
- **Visual Feedback**: Interactive highlighting that responds to playback changes, pauses, and manual navigation through the song

*Experience the magic: Watch lyrics come alive with synchronized highlighting as your music plays*

</details>
</details>

# Installation Guide for Aurras

This guide provides comprehensive instructions for installing Aurras on various operating systems.

## Option 1: Package Managers (Recommended)

When you install Aurras using a system-specific package manager, all necessary dependencies are handled automatically. This is the simplest and recommended method.

### Windows — Chocolatey

```bash
choco install aurras
```

### Linux — AUR (Arch Linux)

```bash
yay -S aurras
```

  > If you don't have `yay` or another AUR helper, consult the [Arch Wiki](https://wiki.archlinux.org/title/AUR_helpers) for installation instructions.

### macOS — Homebrew

```bash
brew install aurras
```

## Option 2: Python Package Index (pip)

When installing Aurras via pip, you'll need to manually ensure that certain external dependencies are present on your system. Aurras requires libmpv (MPV's shared library) for audio playback and ffmpeg for media processing.

### Windows

Aurras comes bundled with all necessary MPV components for Windows, but you will need to install **FFmpeg** separately.

```bash
choco install ffmpeg
```

Once FFmpeg is installed, you can proceed with installing Aurras:

```bash
pip install aurras
```

### Linux & macOS

Before installing Aurras, you must first install MPV and FFmpeg using your system's package manager.

**Ubuntu/Debian:**

```bash
sudo apt update && sudo apt install mpv ffmpeg
```

**Arch Linux:**

```bash
sudo pacman -S mpv ffmpeg
```

**Fedora/RHEL:**

```bash
sudo dnf install mpv ffmpeg
```

**macOS:**

```bash
brew install mpv ffmpeg
```

After ensuring MPV and FFmpeg are installed, you can install Aurras:

```bash
pip install aurras
```

> **Technical Note**: Aurras requires `libmpv` (MPV's shared library) for audio playback. Installing the `mpv` package provides both the executable and the required `libmpv` library that Aurras uses through python-mpv bindings.

<details>
<summary>Development Installation - For contributors</summary>

## Clone and Setup

```bash
# Clone the repository
git clone https://github.com/vedant-asati03/Aurras.git
cd Aurras

# Setup the development environment
python setup_dev_env.py

# Launch in development mode
aurras --help
```

For comprehensive guidelines on contributing to Aurras, please refer to our [Contributions Guide](/CONTRIBUTING.md)

</details>

# Service Setup & Integration

**Connect your music universe** - Aurras currently provides Spotify integration with a flexible architecture designed to support additional music services as the community grows.

## Available Services

Currently supported:

- **Spotify**: Full playlist import and OAuth authentication

```bash
# View Spotify integration options
aurras setup --spotify --help

# Check current integration status  
aurras setup --spotify --status
```

## Spotify Integration

### Quick Setup

```bash
# Run the interactive setup wizard
aurras setup --spotify

# Import your playlists after setup
aurras playlist --import

# Check integration status
aurras setup --spotify --status
```

### Setup Requirements

1. **Create Spotify App**: Visit [Spotify Developer Console](https://developer.spotify.com/dashboard)
   - App name: "Aurras Music Player"
   - Redirect URI: `http://127.0.0.1:8080` *(must be exact)*
   - Copy Client ID and Client Secret

2. **Configure Aurras**: Run `aurras setup --spotify` and enter your credentials

3. **Import Playlists**: Run `aurras playlist --import` to access your Spotify library

### Quick Commands

```bash
aurras setup --spotify --status    # Check connection status
aurras setup --spotify --reset     # Reset credentials  
aurras playlist --import            # Import playlists
```

**Need help?** See the complete [Spotify Integration Guide](/docs/spotify_integration.md) for detailed instructions and troubleshooting.

## Future Services

Aurras is designed with an extensible architecture to support additional music service integrations. **Potential future additions based on community interest:**

- **YouTube Music**: Direct integration with YouTube Music libraries
- **Last.fm**: Scrobbling and music discovery integration  
- **Apple Music**: Library access and playlist synchronization
- **Local Libraries**: Enhanced local music library management
- **Other Platforms**: Community-requested integrations

*Community-driven development: Want to see a specific service integrated? [Request it here](https://github.com/vedant-asati03/Aurras/issues) or contribute to the development!*

</details>

---

# Customization, Settings & Backup Management

Ensure Aurras fits perfectly into your workflow. This section outlines how to effortlessly customize themes, manage core application settings, and safeguard your unique setup with robust backup and restore functionality.

## Theme -

```bash
aurras theme # List out all the themes

aurras theme ocean # Change the app theme to 'ocean'
```

### Crafting Personalized Themes

Aurras empowers you to personalize your player's appearance by creating your own themes. This allows for complete control over the **color scheme**, ensuring your terminal music experience perfectly matches your aesthetic.

To define a custom theme, simply create a `themes.yaml` file within the `~/.aurras/config directory`.

Here's an example of a custom theme configuration:

```yaml
DRACULA:
  name: "DRACULA"
  display_name: "Dracula"
  description: "The famous dark theme with purple, pink, and cyan colors"
  category: "CUSTOM"
  dark_mode: true

  # Core colors
  primary: "#BD93F9"      # Purple
  secondary: "#8BE9FD"    # Cyan
  accent: "#FF79C6"       # Pink

  # UI background colors
  background: "#282A36"   # Dark background
  surface: "#44475A"      # Lighter surface
  panel: "#6272A4"        # Panel color

  # Status colors
  warning: "#FFB86C"      # Orange
  error: "#FF5555"        # Red
  success: "#50FA7B"      # Green
  info: "#8BE9FD"         # Cyan

  # Text colors
  text: "#F8F8F2"         # Foreground
  text_muted: "#6272A4"   # Comment

  # Border colors
  border: "#6272A4"

  # Gradients for enhanced visuals
  title_gradient: ["#BD93F9", "#FF79C6", "#8BE9FD"]
  artist_gradient: ["#8BE9FD", "#50FA7B", "#FFB86C"]
  status_gradient: ["#F8F8F2", "#F8F8F2AA", "#F8F8F277"]
  progress_gradient: ["#BD93F9", "#FF79C6", "#50FA7B"]
  feedback_gradient: ["#50FA7B", "#50FA7BAA", "#50FA7B77"]
  history_gradient: ["#8BE9FD", "#8BE9FDAA", "#8BE9FD77", "#8BE9FD44"]

  # Dim
  dim: "#333366"
```

## Settings -

```bash
aurras settings # List out the app settings

aurras settings --set appearance-settings.display-lyrics no # Updating settings to disable lyrics display

aurras settings --reset # Restore all app settings to their default values
```

### Essential Playback Controls

| Key       | Action                |
| --------- | --------------------- |
| `Space`   | Play/Pause            |
| `n`       | Next song             |
| `b`       | Previous song         |
| `l`       | Toggle lyrics         |
| `↑` / `↓` | Volume up/down        |
| `←` / `→` | Seek backward/forward |

## Backup & Restore -

```bash
aurras backup # List out all the existing backups

aurras backup --create # Create a backup

aurras backup --restore ID # Restore to a specific backup with its unique id
```

# Troubleshooting

Encountering an issue? Here are solutions to some common problems. For more in-depth guidance, refer to our comprehensive [Troubleshooting Guide](/docs/troubleshooting.md).

## Common Issues & Quick Fixes

- **mpv or libmpv not found**:

  **Windows**: Aurras includes bundled MPV DLLs, so this error shouldn't occur. If you see MPV-related errors, try reinstalling with `choco upgrade aurras`.

  **Linux/macOS**:

  - If installed via **package manager** (AUR, Homebrew): This should not happen as dependencies are automatically managed. Try reinstalling: `yay -S aurras` or `brew reinstall aurras`
  - If installed via **pip**: Install MPV manually first:

  ```bash
  # Fedora/RHEL
  sudo dnf install mpv
  
  # Debian/Ubuntu  
  sudo apt install mpv
  
  # Arch Linux
  sudo pacman -S mpv
  
  # macOS
  brew install mpv
  ```

  > **Technical Detail**: Aurras uses python-mpv bindings which load `libmpv` dynamically. You need the shared library (`libmpv.so` on Linux, `libmpv.dylib` on macOS), which is provided by the main MPV package.

- **Display Information Not Updating During Playback**:

  *If the player's display freezes or fails to update song progress and information, this often relates to your slow internet connection.*

  1. Try replaying the song: Sometimes despite a good internet connection an error can occur with loading of the display.
  2. Check your Internet Connection: Your internet might be slow, maybe try switching to a different one.

### Further Assistance

For more detailed troubleshooting, including specific error codes, advanced scenarios, and solutions to less common issues, please consult the comprehensive [Troubleshooting Guide](/docs/troubleshooting.md).

# Uninstall

Need to remove Aurras from your system? We've made it easy with our built-in self-management command that safely removes all traces of the application.

```bash
# Using built-in uninstall command (recommended)
aurras self --uninstall
```

**Package-only removal will:**

- **Safely remove** the Aurras package from your system
- **Preserve your data** (songs, playlists, history, spotify credentials, settings, themes)
- **Clean up** pip package references and dependencies

*<u>Warning</u>: Complete data removal will permanently delete all your songs, playlists, history, spotify credentials, settings, and themes. This action cannot be undone.*

## Troubleshooting Uninstall Issues

- **Permission errors**: You may need to use `sudo` on Linux/macOS or run as administrator on Windows

# Contributing

Aurras is a new project with huge ambitions, and we're just getting started! **Your contributions are incredibly valuable in shaping its future and making it even better**. We warmly welcome all ideas and help. Here's how you can join in:

## Quick Contribution Setup

```bash
git clone https://github.com/vedant-asati03/Aurras.git
cd Aurras

# Set up development environment
python setup_dev_env.py
```

## Areas for Contribution

**Code Contributions:**

- Song batch-based search implementation
- New music source integrations
- TUI improvements and new widgets
- Lyrics integration improvements

**Non-Code Contributions:**

- Documentation and tutorials
- Bug reports and testing
- Design and UX improvements
- Community support

### Development Guidelines

We follow these standards:

- **Python**: PEP 8 with Black formatting
- **Testing**: Comprehensive test coverage required
- **Documentation**: Update docs for user-facing changes
- **Commit Style**: Follow [Conventional Commits](https://www.conventionalcommits.org/)

For detailed guidelines, see our [Contributing Guide](CONTRIBUTING.md).

# License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Third-Party Components

Aurras comes alive thanks to these amazing open-source projects. Huge shoutout to their creators and maintainers:

- **Textual**: The foundational framework for rich Text User Interfaces (MIT License)
- **Rich**: Enhances terminal output with vibrant formatting and styling (MIT License)
- **Spotipy**: Facilitates seamless integration with the Spotify API (MIT License)
- **Spotdl**: Powers high-quality song downloads from streaming services (MIT License)
- **Yt-dlp**: Used for robust song searching on YouTube (Unlicense)
- **Syncedlyrics**: For accurate, real-time synchronized lyrics fetching (MIT License)
- **Python-mpv**: Python bindings for libmpv, bundled directly for seamless integration (GPL v2+ / LGPL v2.1+)
- **Libmpv**: The high-performance media playback library from MPV project (GPL v2+)

---

**Made with ❤️ by the Aurras Community**

[⭐ Star us on GitHub](https://github.com/vedant-asati03/Aurras) • [🐛 Report Bug](https://github.com/vedant-asati03/Aurras/issues) • [💡 Request Feature](https://github.com/vedant-asati03/Aurras/issues)
