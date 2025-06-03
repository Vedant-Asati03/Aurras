"""
Simplified self processor for Aurras CLI.

This module handles self-management commands such as updating,
uninstalling, and getting information about the Aurras installation.
Uses a simplified approach focusing on pip and development installations.
"""

import sys
import shutil
import tomllib
import subprocess
from pathlib import Path
from typing import Tuple
from importlib.metadata import version, PackageNotFoundError

import aurras
from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.utils.path_manager import _path_manager
from aurras.utils.decorators import with_error_handling

logger = get_logger("aurras.command.processors.self", log_to_console=False)
PROJECT_ROOT = Path(aurras.__file__).resolve().parents[1]


class SelfProcessor:
    """Simplified self-management processor."""

    def __init__(self):
        """Initialize the self processor."""
        self.is_development = self._is_development_install()

    def _is_development_install(self) -> bool:
        """Check if this is a development installation."""
        dev_indicators = [
            PROJECT_ROOT / "pyproject.toml",
            PROJECT_ROOT / ".git",
            PROJECT_ROOT / "setup_dev_env.py",
        ]
        return any(indicator.exists() for indicator in dev_indicators)

    def _retrieve_running_version(self) -> Tuple[str, str]:
        """
        Determine the running version of Aurras.

        Returns:
            tuple: (version_string, source_description)
        """
        try:
            if current_version := version("aurras"):
                return (current_version, "Running from installed package")

            return ("Unknown (installed)", "Running from installed package")

        except PackageNotFoundError:
            return (
                "Unknown",
                "Running from unknown source (Check your package manager)",
            )

    @with_error_handling
    def get_version_info(self) -> int:
        """Display version and installation information."""
        try:
            current_version, source = self._retrieve_running_version()
            build_type = "Development" if self.is_development else "Package"

            installation_info = [
                ("Version", current_version),
                ("Status", source),
                ("Installation Path", str(PROJECT_ROOT)),
                ("Installation Type", build_type),
            ]

            from aurras.utils.console.renderer import ListDisplay

            list_display = ListDisplay(
                items=installation_info,
                title="Aurras Installation Information",
                use_table=False,
                show_header=False,
            )
            console.print(list_display.render())
            return 0

        except Exception as e:
            console.print_error(f"Failed to get version information: {e}")
            return 1

    def _show_manual_update_instructions(self):
        """Show manual update instructions."""
        console.print_info("\nManual update options:")
        console.print_info("  pip install --upgrade aurras")
        console.print_info("  # OR")
        console.print_info("  brew upgrade aurras  # if installed via Homebrew")
        console.print_info("  # OR")
        console.print_info("  # Use your system package manager")

    # @with_error_handling
    # def update(self) -> int:
    #     """Update Aurras using the most common approach."""
    #     if self.is_development:
    #         console.print_info("Development installation detected.")
    #         console.print_info("To update:")
    #         console.print_info("  • Run 'git pull' to get latest changes")
    #         console.print_info(
    #             "  • Or reinstall from PyPI: pip install --upgrade aurras"
    #         )
    #         return 0

    #     try:
    #         result = subprocess.run(
    #             [sys.executable, "-m", "pip", "install", "--upgrade", "aurras"],
    #             check=False,
    #             capture_output=True,
    #             text=True,
    #         )

    #         if result.returncode == 0:
    #             console.print_success("Aurras updated successfully!")
    #             console.print_info(
    #                 "Please restart your terminal or run 'aurras --version' to verify the new version."
    #             )
    #             return 0
    #         else:
    #             console.print_warning("Pip update failed or not available.")
    #             self._show_manual_update_instructions()
    #             return 1

    #     except Exception as e:
    #         console.print_error(f"Update failed: {e}")
    #         self._show_manual_update_instructions()
    #         return 1

    @with_error_handling
    def uninstall(self) -> int:
        """
        Uninstall Aurras with user guidance.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        if self.is_development:
            console.print_info("Development installation - just delete the directory")
            console.print_info(f"Directory: {PROJECT_ROOT}")
            return 0

        remove_data = console.confirm("Remove all Aurras data as well?", default=False)

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", "aurras"],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                console.print_success("Aurras uninstalled successfully!")
            else:
                console.print_warning("Uninstallation failed or not available.")
                console.print_info(
                    "Your installation might not have been done via pip."
                )
                return 1

        except Exception as e:
            console.print_error(f"Uninstallation failed: {e}")
            return 1

        if remove_data:
            try:
                shutil.rmtree(_path_manager.app_dir)

            except OSError as e:
                print("Error: %s - %s." % (e.filename, e.strerror))
                return 1

            console.print_warning("Disclaimer: Your backup data is still intact.")
            console.style_text(
                text="Check if you have a backup by running: aurras backup --list",
                style_key="text_muted",
                print_it=True,
            )

        return 0

    @with_error_handling
    def check_dependencies(self) -> int:
        """
        Check if all required dependencies are properly installed.
        Uses pyproject.toml as the single source of truth.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        pyproject_file = PROJECT_ROOT / "pyproject.toml"

        if not pyproject_file.exists():
            console.print_error("pyproject.toml not found!")
            return 1

        try:
            with open(pyproject_file, "rb") as f:
                pyproject_data = tomllib.load(f)

            dependencies = pyproject_data.get("project", {}).get("dependencies", [])

            if not dependencies:
                console.print_warning("No dependencies found in pyproject.toml")
                return 0

            required_packages = []
            for dep in dependencies:
                if isinstance(dep, str) and dep.strip():
                    package_name = (
                        dep.strip()
                        .split(">=")[0]
                        .split("==")[0]
                        .split("~=")[0]
                        .split("!=")[0]
                        .split("<")[0]
                        .split(">")[0]
                        .strip()
                    )
                    if package_name:
                        required_packages.append(package_name)

        except Exception as e:
            console.print_error(f"Failed to parse pyproject.toml: {e}")
            return 1

        missing_deps = []
        for package in required_packages:
            try:
                version(package)
            except PackageNotFoundError:
                missing_deps.append(package)

        if not missing_deps:
            console.print_success(
                f"All {len(required_packages)} dependencies are properly installed!"
            )
            console.print_info("Source: pyproject.toml")
            return 0
        else:
            console.print_warning(
                f"Missing dependencies ({len(missing_deps)} out of {len(required_packages)}):"
            )
            for dep in missing_deps:
                console.print_warning(f"   {dep}")

            console.print_info("\nTo install missing dependencies:")
            if self.is_development:
                console.print_info("  pip install -e .")
                console.print_info("  # or")

            console.print_info(f"  pip install {' '.join(missing_deps)}")
            return 1
