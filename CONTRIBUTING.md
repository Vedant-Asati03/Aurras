# Contributing to Aurras

Thank you for considering contributing to Aurras! This document outlines the process for contributing to the project and the standards we follow.

## Table of Contents

- [Contributing to Aurras](#contributing-to-aurras)
  - [Table of Contents](#table-of-contents)
  - [Code of Conduct](#code-of-conduct)
  - [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
    - [Required Software](#required-software)
    - [External Dependencies](#external-dependencies)
  - [Development Environment](#development-environment)
  - [Project Architecture](#project-architecture)
    - [Core Components](#core-components)
    - [Dual Interface System](#dual-interface-system)
    - [Key Features to Understand](#key-features-to-understand)
  - [Coding Standards](#coding-standards)
    - [Code Formatting and Style](#code-formatting-and-style)
    - [Before Submitting Changes](#before-submitting-changes)
    - [Configuration](#configuration)
  - [Testing](#testing)
    - [Running Tests](#running-tests)
    - [Writing Tests](#writing-tests)
  - [Pull Request Process](#pull-request-process)
    - [PR Requirements Checklist](#pr-requirements-checklist)
  - [Branch Naming Convention](#branch-naming-convention)
  - [Areas for Contribution](#areas-for-contribution)
    - [Code Contributions](#code-contributions)
    - [Non-Code Contributions](#non-code-contributions)
    - [Getting Started Areas](#getting-started-areas)
  - [Development Tips](#development-tips)
    - [Debugging](#debugging)
    - [Working with Themes](#working-with-themes)
    - [Testing Your Changes](#testing-your-changes)
  - [Versioning](#versioning)
    - [Version Format](#version-format)
    - [Release Process](#release-process)
  - [Questions or Need Help?](#questions-or-need-help)

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/vedant-asati03/Aurras.git`
3. Set up the development environment as described below
4. Create a branch for your changes

## Prerequisites

Before setting up the development environment, ensure you have the following installed:

### Required Software

1. **Python 3.12 or higher**

   ```bash
   python --version  # Should show 3.12 or higher
   ```

2. **UV Package Manager** (recommended for dependency management)

   ```bash
   # Linux/macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Or visit: https://github.com/astral-sh/uv#installation
   ```

### External Dependencies

Aurras requires external media tools for audio processing and playback:

1. **MPV Media Player**

   ```bash
   # Ubuntu/Debian
   sudo apt install mpv
   
   # Arch Linux
   sudo pacman -S mpv
   
   # macOS
   brew install mpv
   
   # Windows (Chocolatey)
   choco install mpv
   ```

2. **FFmpeg** (for audio processing)

   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # Arch Linux
   sudo pacman -S ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows (Chocolatey)
   choco install ffmpeg
   ```

## Development Environment

1. **Clone the repository and navigate to it**

   ```bash
   cd Aurras
   ```

2. **Set up the development environment using the provided script**

   ```bash
   python setup_dev_env.py
   ```

   This script will:
   - Create a virtual environment using `uv`
   - Activate the virtual environment
   - Install all project dependencies from `requirements.txt`
   - Install development tools (pytest, black, isort, flake8, mypy)
   - Install the package in development mode

3. **Verify the installation**

   ```bash
   # Test the CLI interface
   python -m aurras.aurras_cli --help

   # Or test using the installed command
   aurras --help
   ```

## Project Architecture

Aurras is designed with a modular architecture supporting multiple interfaces:

### Core Components

- **`aurras/core/`** - Core functionality including player, downloader, settings, and playlist management
- **`aurras/services/`** - External service integrations (YouTube, Spotify, lyrics)
- **`aurras/ui/`** - User interface components and input handling
- **`aurras/tui/`** - Text User Interface implementation using Textual
- **`aurras/themes/`** - Theme system with color management and definitions
- **`aurras/utils/`** - Utility functions and helper modules

### Dual Interface System

Aurras offers two primary interfaces:

1. **Command-Line Interface (CLI)** - `aurras.aurras_cli`
   - Lightweight, direct command execution
   - Interactive and non-interactive modes
   - Perfect for scripting and power users

2. **Text User Interface (TUI)** - `aurras.aurras_tui`
   - Rich, interactive terminal interface built with Textual
   - Real-time display of playback status, queue, and metadata
   - Mouse and keyboard support

### Key Features to Understand

- **Multi-Source Integration**: YouTube, Spotify, and local music
- **Advanced Theme System**: 10+ built-in themes with full customization
- **Smart Search**: Context-aware search with command palette
- **Lyrics Integration**: Real-time synced lyrics with highlighting
- **Playlist Management**: Smart creation and organization

## Coding Standards

We follow these coding standards to maintain code quality and consistency:

### Code Formatting and Style

- **Code formatting** with [Black](https://black.readthedocs.io/en/stable/) (line length: 88)
- **Import sorting** with [isort](https://pycqa.github.io/isort/) (Black profile)
- **Linting** with [Flake8](https://flake8.pycqa.org/en/latest/)
- **Type checking** with [Mypy](https://mypy.readthedocs.io/) (Python 3.12+)
- **Docstrings** using Google style format

### Before Submitting Changes

Run the following commands to ensure code quality:

```bash
# Format code
black .
isort .

# Check for linting issues
flake8

# Type checking
mypy .
```

### Configuration

The project includes configuration for all tools in `pyproject.toml`:

- **Black**: Line length 88, profile compatibility with isort
- **isort**: Black profile for import sorting
- **Mypy**: Python 3.12 target with strict type checking

## Testing

The project uses pytest for testing. Currently, the test infrastructure is being developed.

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_specific.py
```

### Writing Tests

When contributing new features:

1. Write tests for new functionality
2. Ensure all existing tests pass
3. Aim for good test coverage of critical paths
4. Follow the existing test structure in `tests/`

**Note**: The testing framework is currently being expanded. Check the `tests/` directory for the latest examples and patterns.

## Pull Request Process

1. **Update Documentation**: Update the README.md and any relevant documentation with details of your changes
2. **Update Changelog**: Add notes about your changes to the CHANGELOG.md following the established format
3. **Code Quality**: Ensure all code quality checks pass (Black, isort, Flake8, Mypy)
4. **Testing**: Make sure any existing tests pass and add tests for new functionality where appropriate
5. **Review Process**: The PR should be reviewed by at least one maintainer
6. **Merge**: Once approved, a maintainer will merge your PR

### PR Requirements Checklist

- [ ] Code follows the project's coding standards
- [ ] All code quality tools pass (Black, isort, Flake8, Mypy)
- [ ] Documentation is updated for user-facing changes
- [ ] CHANGELOG.md is updated with your changes
- [ ] Tests are added/updated for new functionality
- [ ] PR description clearly explains the changes

## Branch Naming Convention

Use descriptive branch names that clearly indicate the purpose of your changes:

- `feature/my-new-feature` - For new features
- `bugfix/issue-description` - For bug fixes
- `docs/what-is-changing` - For documentation updates
- `refactor/what-is-changing` - For code refactoring
- `theme/new-theme-name` - For new themes or theme improvements
- `ui/component-improvements` - For UI/UX improvements

## Areas for Contribution

We welcome contributions in many areas! Here are some ways you can help:

### Code Contributions

**High Priority:**

- **Testing Infrastructure**: Expand the test suite and improve coverage
- **TUI Enhancements**: New widgets, improved responsiveness, better layouts
- **Music Source Integration**: Support for additional streaming platforms
- **Performance Optimizations**: Memory usage, startup time, search speed

**Medium Priority:**

- **Lyrics Improvements**: Better synchronization, more sources, offline caching
- **Theme System**: New themes, theme editor, better customization options
- **Playlist Features**: Advanced sorting, smart playlists, import/export
- **Search Enhancements**: Better fuzzy search, filters, recommendation algorithms

**Enhancement Ideas:**

- **Mobile Support**: Terminal-based mobile interface considerations
- **Plugin System**: Architecture for third-party extensions
- **Advanced Audio**: Equalizer, audio effects, crossfading
- **Social Features**: Playlist sharing, collaborative playlists

### Non-Code Contributions

**Documentation:**

- Improve installation guides for different operating systems
- Create video tutorials and usage examples
- Write detailed API documentation
- Translate documentation to other languages

**Community:**

- Help answer questions in issues and discussions
- Test new features and report bugs
- Share Aurras with others and gather feedback
- Create example configurations and themes

**Design & UX:**

- Design new themes and color schemes
- Improve UI/UX flow and accessibility
- Create icons and visual assets
- Conduct usability testing

### Getting Started Areas

If you're new to the project, consider starting with:

1. **Documentation improvements** - Good way to learn the codebase
2. **Theme creation** - Self-contained and creative
3. **Bug fixes** - Check the issues for "good first issue" labels
4. **Testing** - Help expand the test coverage

## Development Tips

### Debugging

```bash
# Run with debug logging
AURRAS_LOG_LEVEL=DEBUG aurras

# Check log files
tail -f ~/.local/share/aurras/logs/aurras.log
```

### Working with Themes

```bash
# Test theme changes live
aurras # Start the app
# In app: >theme switch <theme_name>
```

### Testing Your Changes

```bash
# Quick functionality test
aurras "test song"

# Test TUI mode
aurras-tui

# Test specific components
python -c "from aurras.core.player import Player; print('Player OK')"
```

## Versioning

We use [Semantic Versioning (SemVer)](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/vedant-asati03/Aurras/tags).

### Version Format

- **MAJOR.MINOR.PATCH** (e.g., 1.1.1)
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backwards compatible manner
- **PATCH**: Backwards compatible bug fixes

### Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Create and push a version tag
4. GitHub Actions will automatically build and publish to PyPI

---

## Questions or Need Help?

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/vedant-asati03/Aurras/issues)
- **Discussions**: General questions and community discussions via [GitHub Discussions](https://github.com/vedant-asati03/Aurras/discussions)
- **Documentation**: Check the [docs/](docs/) directory for detailed documentation

Thank you for contributing to Aurras! 🎵
