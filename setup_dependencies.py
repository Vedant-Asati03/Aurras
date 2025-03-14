#!/usr/bin/env python3
"""
Setup script to install all required dependencies for Aurras.
"""

import sys
import subprocess
import os
from pathlib import Path

# Required Python packages
REQUIRED_PACKAGES = [
    "prompt-toolkit",
    "rich",
    "spotipy",
    "questionary",
    "ytmusicapi",
    "PyYAML",
    "sqlitedict",
]

# Optional packages for enhanced functionality
OPTIONAL_PACKAGES = [
    "lyrics-extractor",  # For lyrics functionality
    "googletrans==4.0.0-rc1",  # For translation functionality
    "keyboard",  # For keyboard shortcuts
    "spotdl",  # For downloading songs
]


def install_package(package, optional=False):
    """Install a Python package using pip."""
    print(f"Installing {'optional' if optional else 'required'} package: {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to install {package}")
        if not optional:
            print(
                f"This is a required package and the application may not work properly without it."
            )
        return False


def check_external_dependencies():
    """Check if required external dependencies are installed."""
    missing = []

    # Check for mpv
    try:
        subprocess.run(
            ["mpv", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("✓ MPV is installed")
    except FileNotFoundError:
        missing.append("mpv")
        print("✗ MPV is not installed")

    # Check for ffmpeg
    try:
        subprocess.run(
            ["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("✓ FFmpeg is installed")
    except FileNotFoundError:
        missing.append("ffmpeg")
        print("✗ FFmpeg is not installed")

    return missing


def main():
    """Main function to set up dependencies."""
    print("\n=== Aurras Dependencies Setup ===\n")

    # Check for external dependencies first
    missing = check_external_dependencies()
    if missing:
        print("\nMissing external dependencies:")
        for dep in missing:
            print(f"- {dep}")

        print("\nPlease install them using your package manager:")
        print("Ubuntu/Debian: sudo apt install mpv ffmpeg")
        print("Arch Linux: sudo pacman -S mpv ffmpeg")
        print("Fedora: sudo dnf install mpv ffmpeg")
        print("macOS (Homebrew): brew install mpv ffmpeg")
        print("Windows: Use the installer from https://mpv.io/installation/")

        choice = input("\nContinue with Python package installation anyway? (y/n): ")
        if choice.lower() != "y":
            print("Setup aborted.")
            return 1

    # Install required Python packages
    print("\nInstalling required Python packages...")
    success = True
    for package in REQUIRED_PACKAGES:
        if not install_package(package):
            success = False

    # Install optional Python packages
    print("\nDo you want to install optional packages for enhanced functionality?")
    print("These include lyrics display, translation, and keyboard shortcuts.")
    choice = input("Install optional packages? (y/n): ")

    if choice.lower() == "y":
        print("\nInstalling optional Python packages...")
        for package in OPTIONAL_PACKAGES:
            install_package(package, optional=True)

    if success:
        print("\nAll required dependencies successfully installed!")
        print("You can now run Aurras with: aurras")

        if choice.lower() != "y":
            print("\nNote: Some features (lyrics, translation) will be limited.")
            print("You can install optional packages later with:")
            print(f"  {sys.executable} {os.path.abspath(__file__)} --optional")
    else:
        print("\nSome dependencies could not be installed.")
        print("Please check the error messages above and try again.")
        return 1

    return 0


if __name__ == "__main__":
    # Check if --optional flag is passed
    if len(sys.argv) > 1 and sys.argv[1] == "--optional":
        print("Installing optional packages only...")
        for package in OPTIONAL_PACKAGES:
            install_package(package, optional=True)
        sys.exit(0)

    sys.exit(main())
