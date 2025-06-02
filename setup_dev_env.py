#!/usr/bin/env python3
"""
Cross-platform development environment setup for Aurras.

This script works on Linux, macOS, and Windows.
"""

import sys
import platform
import subprocess


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    if description:
        print(f"Running: {description}...")

    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print(f"Success: {description or 'Command'} completed")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error: {description or 'Command'} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")

        return False


def get_activation_command():
    """Get the correct activation command based on OS."""
    if platform.system() == "Windows":
        return ".venv\\Scripts\\activate"
    else:
        return "source .venv/bin/activate"


def main():
    """Set up development environment."""
    print("Setting up Aurras development environment...")
    print(f"Platform: {platform.system()} {platform.release()}")

    # Check if uv is installed
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        print("uv is already installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: uv not found. Please install uv first:")
        print("   Linux/macOS: curl -LsSf https://astral.sh/uv/install.sh | sh")
        print(
            "   Windows: powershell -ExecutionPolicy ByPass -c 'irm https://astral.sh/uv/install.ps1 | iex'"
        )
        print("   Or visit: https://github.com/astral-sh/uv#installation")
        sys.exit(1)

    # Create virtual environment and install dependencies from pyproject.toml
    if not run_command(
        "uv sync", "Creating virtual environment and installing dependencies"
    ):
        sys.exit(1)

    # Install development packages
    dev_packages = "pytest black isort flake8 mypy"
    if not run_command(
        f"uv add --dev {dev_packages}", "Installing development packages"
    ):
        sys.exit(1)

    print("\nDevelopment environment setup complete!")
    print(f"To activate the environment, run: {get_activation_command()}")
    print("Then launch Aurras with: python -m aurras")


if __name__ == "__main__":
    main()
