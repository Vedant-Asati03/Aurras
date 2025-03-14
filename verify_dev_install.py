#!/usr/bin/env python3
"""
Simple script to verify that Aurras is installed in development mode.
"""

import os
import sys
import importlib.util
import subprocess


def get_package_location(package_name):
    """Get the location of an installed package."""
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        return None
    return spec.origin


def get_command_location(command):
    """Get the location of a command in PATH."""
    try:
        result = subprocess.run(
            ["which", command], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def main():
    package_location = get_package_location("aurras")
    command_location = get_command_location("aurras")

    project_dir = os.path.abspath(os.path.dirname(__file__))

    print(f"Project directory:   {project_dir}")
    print(f"Package location:    {package_location}")
    print(f"Command location:    {command_location}")

    if package_location and project_dir in package_location:
        print("\n[✓] Aurras is correctly installed in development mode!")
        print("    Changes to your code will be immediately available.")
    else:
        print("\n[✗] Aurras is NOT installed in development mode.")
        print("    Run './dev_install.sh' to set up development mode.")


if __name__ == "__main__":
    main()
