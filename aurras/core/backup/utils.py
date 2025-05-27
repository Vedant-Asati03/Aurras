"""
Backup utility functions.

This module provides helper functions for the backup system.
"""

import os
import sys
import time
import json
import shutil
from pathlib import Path
from datetime import datetime

from aurras.utils.logger import get_logger

logger = get_logger("aurras.core.backup.utils", log_to_console=False)


def get_platform_specific_backup_dir():
    """
    Get the default backup directory for the current platform.

    Returns:
        Path: Path object pointing to the appropriate backup directory
    """
    home = Path.home()

    match sys.platform:
        case "win32" | "cygwin":  # Windows
            base_dir = Path(
                os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local"))
            )
            return base_dir / "aurras" / "backup"

        case "darwin":  # macOS
            return home / "Library" / "Application Support" / "aurras" / "backup"

        case s if s.startswith("linux"):  # Linux
            # Check if using XDG
            xdg_data_home = os.environ.get("XDG_DATA_HOME")

            if xdg_data_home:
                return Path(xdg_data_home) / "aurras" / "backup"
            return home / ".local" / "share" / "aurras" / "backup"

        case _:  # Other platforms
            logger.warning("Unsupported platform. Defaulting to home directory.")
            return home / ".aurras" / "backup"


def resolve_backup_dir(backup_path: str):
    """
    Resolve the backup directory from settings.

    Args:
        backup_path: The backup_dir setting value

    Returns:
        Path: The resolved backup directory path
    """
    if backup_path and backup_path.lower() != "default":
        abs_path = Path(backup_path).expanduser()
        return abs_path

    return get_platform_specific_backup_dir()


def create_backup_id():
    """
    Create a unique backup ID based on timestamp.

    Returns:
        str: A unique backup ID
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_readable_size(size_bytes):
    """
    Convert bytes to a human-readable size string.

    Args:
        size_bytes (int): Size in bytes

    Returns:
        str: Human-readable size (e.g. "2.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024 or unit == "TB":
            if unit == "B":
                return f"{size_bytes} {unit}"
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def validate_backup_metadata(metadata):
    """
    Validate backup metadata for consistency.

    Args:
        metadata (dict): The metadata to validate

    Returns:
        bool: True if metadata is valid, False otherwise
    """
    required_fields = ["timestamp", "version", "date", "items"]

    # Check for required fields
    for field in required_fields:
        if field not in metadata:
            logger.error(f"Missing required field in metadata: {field}")
            return False

    # Check timestamp is a number
    if not isinstance(metadata["timestamp"], (int, float)):
        logger.error("Timestamp is not a number")
        return False

    # Check items is a dictionary
    if not isinstance(metadata["items"], dict):
        logger.error("Items field is not a dictionary")
        return False

    return True


def safe_copy(src, dst, retries=3, delay=0.5):
    """
    Safely copy a file with retry logic.

    Args:
        src (Path): Source file path
        dst (Path): Destination file path
        retries (int): Number of retries on failure
        delay (float): Delay between retries in seconds

    Returns:
        bool: True if copy was successful, False otherwise
    """
    for attempt in range(retries):
        try:
            # Ensure destination directory exists
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            logger.warning(f"Copy attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logger.error(f"Failed to copy {src} to {dst} after {retries} attempts")
                return False


def read_backup_history(metadata_dir):
    """
    Read the backup history file.

    Args:
        metadata_dir (Path): Path to the metadata directory

    Returns:
        dict: The backup history, or an empty dict if not found
    """
    history_file = metadata_dir / "backup_history.json"

    if not history_file.exists():
        return {"backups": []}

    try:
        with open(history_file, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading backup history: {e}")
        return {"backups": []}


def update_backup_history(metadata_dir, backup_id, metadata, status="completed"):
    """
    Update the backup history file with a new backup.

    Args:
        metadata_dir (Path): Path to the metadata directory
        backup_id (str): The ID of the backup
        metadata (dict): The backup metadata
        status (str): The status of the backup (completed, failed, etc.)

    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        metadata_dir.mkdir(parents=True, exist_ok=True)
        history_file = metadata_dir / "backup_history.json"

        # Read existing history
        history = read_backup_history(metadata_dir)

        # Add new backup info
        backup_info = {
            "id": backup_id,
            "timestamp": metadata["timestamp"],
            "date": metadata["date"],
            "status": status,
            "items": list(metadata["items"].keys()) if "items" in metadata else [],
        }

        # Ensure we don't duplicate entries
        history["backups"] = [b for b in history["backups"] if b["id"] != backup_id]
        history["backups"].append(backup_info)

        # Sort by timestamp (newest first)
        history["backups"].sort(key=lambda x: x["timestamp"], reverse=True)

        # Write updated history
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)

        return True
    except Exception as e:
        logger.error(f"Error updating backup history: {e}")
        return False


def create_symlink_to_latest(backup_dir: Path, backup_id: str):
    """
    Create a symlink to the latest successful backup.

    Args:
        backup_dir (Path): The base backup directory
        backup_id (str): The ID of the latest backup

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        current_link: str = backup_dir / "current"
        target: str = backup_dir / "backups" / backup_id

        # Remove existing symlink if it exists
        if current_link.exists():
            if current_link.is_symlink():
                current_link.unlink()

            else:
                logger.error("'current' exists but is not a symlink")
                return False

        # Create relative symlink (more portable)
        os.symlink(os.path.relpath(target, current_link.parent), current_link)
        return True

    except Exception as e:
        logger.error(f"Error creating symlink to latest backup: {e}")
        return False
