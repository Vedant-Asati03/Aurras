"""
Storage backend for the backup system.

This module provides the storage backend abstraction for the Aurras backup system.
"""

import json
import shutil
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, Any

from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.utils.path_manager import _path_manager
from aurras.core.backup.utils import (
    resolve_backup_dir,
    update_backup_history,
    create_symlink_to_latest,
)

logger = get_logger("aurras.core.backup.storage", log_to_console=False)


class StorageBackend(ABC):
    """Abstract base class for backup storage backends."""

    @abstractmethod
    def save_backup(self, backup_id, files_to_backup, metadata):
        """
        Save a backup with the given data and metadata.

        Args:
            backup_id (str): Unique identifier for the backup
            files_to_backup (dict): Dict mapping source paths to backup destinations
            metadata (dict): Backup metadata

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_backup(self, backup_id):
        """
        Retrieve a backup by ID.

        Args:
            backup_id (str): ID of the backup to retrieve

        Returns:
            dict: Backup data including path and metadata
        """
        pass

    @abstractmethod
    def list_backups(self):
        """
        List all available backups.

        Returns:
            list: List of backup metadata dictionaries
        """
        pass

    @abstractmethod
    def delete_backup(self, backup_id):
        """
        Delete a backup by ID.

        Args:
            backup_id (str): ID of the backup to delete

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def cleanup_old_backups(self, keep_count):
        """
        Remove old backups, keeping the most recent ones.

        Args:
            keep_count (int): Number of most recent backups to keep

        Returns:
            int: Number of backups removed
        """
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend for backups."""

    def __init__(self):
        """
        Initialize the local storage backend.

        Args:
            settings: The application settings
        """
        self.backup_dir = resolve_backup_dir(SETTINGS.backup.backup_dir)

        self.backups_storage_dir = self.backup_dir / Path(
            _path_manager.backups_storage_dir
        )
        self.metadata_dir = self.backup_dir / Path(_path_manager.backup_metadata_dir)
        self.logs_dir = self.backup_dir / Path(_path_manager.backup_logs_dir)

        self._mkdir(self.backup_dir)
        self._mkdir(self.backups_storage_dir)
        self._mkdir(self.metadata_dir)
        self._mkdir(self.logs_dir)

    def _mkdir(self, path: Path):
        """
        Create a directory if it doesn't exist.

        Args:
            path (Path): Path to the directory to create
        """
        try:
            path.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")

    def save_backup(
        self,
        backup_id: str,
        files_to_backup: Dict[Path, str],
        metadata: Dict[str, Any],
    ):
        """
        Save a backup with the given data and metadata.

        Args:
            backup_id (str): Unique identifier for the backup
            files_to_backup (dict): Dict mapping source paths to backup destinations
            metadata (dict): Backup metadata

        Returns:
            bool: True if successful, False otherwise
        """
        backup_directory = self.backups_storage_dir / backup_id

        try:
            self._mkdir(backup_directory)

            for source_file_path, relative_backup_path in files_to_backup.items():
                if not source_file_path.exists():
                    logger.warning(f"Source file does not exist: {source_file_path}")
                    continue

                destination = backup_directory / relative_backup_path
                self._mkdir(destination.parent)

                try:
                    shutil.copy2(source_file_path, destination)
                except Exception as e:
                    logger.error(
                        f"Failed to copy {source_file_path} to {destination}: {e}"
                    )
                    return False

            with open(backup_directory / "metadata.json", "w") as metadata_file:
                json.dump(metadata, metadata_file, indent=2)

            update_backup_history(self.metadata_dir, backup_id, metadata)
            create_symlink_to_latest(self.backup_dir, backup_id)

            return True
        except Exception as e:
            logger.error(f"Error saving backup: {e}")
            return False

    def get_backup(self, backup_id):
        """
        Retrieve a backup by ID.

        Args:
            backup_id (str): ID of the backup to retrieve

        Returns:
            dict: Backup data including path and metadata, or None if not found
        """
        backup_path = self.backups_storage_dir / backup_id

        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_id}")
            return None

        metadata_path = backup_path / "metadata.json"
        if not metadata_path.exists():
            logger.error(f"Metadata not found for backup: {backup_id}")
            return None

        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            return {"id": backup_id, "path": backup_path, "metadata": metadata}

        except Exception as e:
            logger.error(f"Error retrieving backup {backup_id}: {e}")
            return None

    def list_backups(self):
        """
        List all available backups.

        Returns:
            list: List of backup metadata dictionaries
        """
        backups = []

        try:
            for item in self.backups_storage_dir.iterdir():
                if item.is_dir():
                    backup_id = item.name
                    metadata_path = item / "metadata.json"

                    if metadata_path.exists():
                        try:
                            with open(metadata_path, "r") as f:
                                metadata = json.load(f)

                            backups.append(
                                {
                                    "id": backup_id,
                                    "path": str(item),
                                    "metadata": metadata,
                                }
                            )
                        except Exception as e:
                            logger.warning(
                                f"Error reading metadata for backup {backup_id}: {e}"
                            )

            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x["metadata"].get("timestamp", 0), reverse=True)

            return backups
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []

    def delete_backup(self, backup_id):
        """
        Delete a backup by ID.

        Args:
            backup_id (str): ID of the backup to delete

        Returns:
            bool: True if successful, False otherwise
        """
        backup_path = self.backups_storage_dir / backup_id

        if not backup_path.exists():
            logger.warning(f"Backup not found for deletion: {backup_id}")
            return False

        try:
            # Remove the backup directory and all contents
            shutil.rmtree(backup_path)

            # Update backup history
            history_path = self.metadata_dir / "backup_history.json"
            if history_path.exists():
                try:
                    with open(history_path, "r") as f:
                        history = json.load(f)

                    # Remove this backup from history
                    history["backups"] = [
                        b for b in history["backups"] if b["id"] != backup_id
                    ]

                    with open(history_path, "w") as f:
                        json.dump(history, f, indent=2)
                except Exception as e:
                    logger.warning(f"Error updating history after deletion: {e}")

            return True
        except Exception as e:
            logger.error(f"Error deleting backup {backup_id}: {e}")
            return False

    def cleanup_old_backups(self, keep_count):
        """
        Remove old backups, keeping the most recent ones.

        Args:
            keep_count (int): Number of most recent backups to keep

        Returns:
            int: Number of backups removed
        """
        try:
            backups = self.list_backups()

            # Keep the most recent backups
            to_delete = backups[keep_count:]

            deleted_count = 0
            for backup in to_delete:
                if self.delete_backup(backup["id"]):
                    deleted_count += 1

            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            return 0
