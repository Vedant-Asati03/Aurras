"""
Backup Manager Module

This module provides functionality for backing up and restoring Aurras data.
"""

import os
import time
import json
import shutil
import sqlite3
import zipfile
from pathlib import Path
from datetime import datetime
import yaml
from rich.console import Console

from ..utils.path_manager import PathManager
from ..core.settings import LoadDefaultSettings

_path_manager = PathManager()
console = Console()


class BackupManager:
    """
    Class for managing backups and restoration of Aurras data.

    This class handles creating backups of user data like history,
    playlists, settings, and cache, as well as restoring from backups.
    """

    def __init__(self):
        """Initialize the BackupManager."""
        self.settings = LoadDefaultSettings().load_default_settings()
        self.backup_dir = self._get_backup_directory()
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _get_backup_directory(self) -> Path:
        """Get the directory where backups should be stored."""
        backup_location = self.settings.get("backup", {}).get(
            "backup-location", "default"
        )

        if backup_location == "default" or not backup_location:
            return _path_manager.construct_path("backups")
        else:
            # Use custom location if specified
            custom_path = Path(backup_location).expanduser()
            custom_path.mkdir(parents=True, exist_ok=True)
            return custom_path

    def _should_backup_automatically(self) -> bool:
        """Check if automatic backup is enabled and due."""
        backup_settings = self.settings.get("backup", {})

        if backup_settings.get("enabled", "yes").lower() != "yes":
            return False

        if backup_settings.get("auto-backup", "yes").lower() != "yes":
            return False

        # Check when the last backup was made
        last_backup_file = self.backup_dir / "last_backup.json"

        if not last_backup_file.exists():
            return True  # No previous backup found

        try:
            with open(last_backup_file, "r") as f:
                last_backup_info = json.load(f)

            last_backup_time = last_backup_info.get("timestamp", 0)
            frequency_days = int(backup_settings.get("backup-frequency", "7"))

            # Convert frequency to seconds
            frequency_seconds = frequency_days * 24 * 60 * 60

            # Check if enough time has passed since the last backup
            return (time.time() - last_backup_time) >= frequency_seconds

        except Exception as e:
            console.print(f"[yellow]Error checking last backup time: {e}[/yellow]")
            return True  # If there's an error, assume backup is needed

    def check_and_backup(self):
        """Check if backup is needed and perform it if so."""
        if self._should_backup_automatically():
            try:
                self.create_backup(show_message=False)
            except Exception as e:
                console.print(f"[yellow]Auto-backup failed: {e}[/yellow]")

    def create_backup(self, manual=False, show_message=True):
        """
        Create a backup of user data.

        Args:
            manual: Whether this is a manual backup request
            show_message: Whether to show status messages
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"aurras_backup_{timestamp}.zip"

        backup_items = self.settings.get("backup", {}).get("backup-items", {})

        if show_message:
            console.print("[cyan]Creating backup...[/cyan]")

        with zipfile.ZipFile(backup_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Always include a metadata file
            metadata = {
                "timestamp": time.time(),
                "date": datetime.now().isoformat(),
                "version": "0.1.1",  # Application version
                "items": {},
            }

            # Backup settings
            if backup_items.get("settings", "yes").lower() == "yes":
                if _path_manager.settings_file.exists():
                    zipf.write(_path_manager.settings_file, "settings.yaml")
                    metadata["items"]["settings"] = True

            # Backup history
            if backup_items.get("history", "yes").lower() == "yes":
                if _path_manager.history_db.exists():
                    zipf.write(_path_manager.history_db, "history.db")
                    metadata["items"]["history"] = True

            # Backup playlists
            if backup_items.get("playlists", "yes").lower() == "yes":
                if _path_manager.saved_playlists.exists():
                    zipf.write(_path_manager.saved_playlists, "playlists.db")
                    metadata["items"]["playlists"] = True

                # Additionally backup downloaded playlists if they exist
                if _path_manager.playlists_dir.exists():
                    for item in _path_manager.playlists_dir.iterdir():
                        if item.is_dir():
                            for song_file in item.iterdir():
                                rel_path = song_file.relative_to(
                                    _path_manager._base_dir
                                )
                                zipf.write(song_file, str(rel_path))

            # Backup cache if enabled
            if backup_items.get("cache", "no").lower() == "yes":
                for cache_file in [
                    _path_manager.cache_db,
                    _path_manager.lyrics_cache_db,
                ]:
                    if cache_file.exists():
                        rel_path = cache_file.name
                        zipf.write(cache_file, rel_path)
                        metadata["items"]["cache"] = True

            # Write metadata to the zip file
            zipf.writestr("metadata.json", json.dumps(metadata, indent=2))

        # Update last backup info
        with open(self.backup_dir / "last_backup.json", "w") as f:
            json.dump({"timestamp": time.time(), "file": str(backup_file)}, f)

        if show_message:
            console.print(f"[green]Backup created: {backup_file}[/green]")

        # Clean up old backups
        self._cleanup_old_backups()

    def _cleanup_old_backups(self, keep=5):
        """
        Remove old backups, keeping the most recent ones.

        Args:
            keep: Number of recent backups to keep
        """
        backup_files = sorted(
            [f for f in self.backup_dir.glob("aurras_backup_*.zip")],
            key=os.path.getmtime,
            reverse=True,
        )

        # Keep the most recent 'keep' backups
        for old_backup in backup_files[keep:]:
            try:
                old_backup.unlink()
            except Exception as e:
                console.print(
                    f"[yellow]Could not remove old backup {old_backup.name}: {e}[/yellow]"
                )

    def restore_from_backup(self, backup_file=None):
        """
        Restore data from a backup file.

        Args:
            backup_file: Path to the backup file to restore from.
                         If None, the latest backup will be used.
        """
        # Find the latest backup if none specified
        if backup_file is None:
            backup_files = sorted(
                [f for f in self.backup_dir.glob("aurras_backup_*.zip")],
                key=os.path.getmtime,
                reverse=True,
            )

            if not backup_files:
                console.print("[yellow]No backup files found.[/yellow]")
                return False

            backup_file = backup_files[0]
        else:
            backup_file = Path(backup_file)
            if not backup_file.exists():
                console.print(f"[red]Backup file not found: {backup_file}[/red]")
                return False

        console.print(f"[cyan]Restoring from backup: {backup_file.name}[/cyan]")

        # Create a temporary directory for extraction
        temp_dir = _path_manager.construct_path("temp_restore")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()

        try:
            # Extract the backup
            with zipfile.ZipFile(backup_file, "r") as zipf:
                zipf.extractall(temp_dir)

            # Read metadata
            with open(temp_dir / "metadata.json", "r") as f:
                metadata = json.load(f)

            # Restore settings
            if (
                metadata.get("items", {}).get("settings")
                and (temp_dir / "settings.yaml").exists()
            ):
                shutil.copy(temp_dir / "settings.yaml", _path_manager.settings_file)
                console.print("[green]✓ Settings restored[/green]")

            # Restore history
            if (
                metadata.get("items", {}).get("history")
                and (temp_dir / "history.db").exists()
            ):
                # Close any open connections first
                time.sleep(0.5)  # Give time for connections to close
                shutil.copy(temp_dir / "history.db", _path_manager.history_db)
                console.print("[green]✓ Play history restored[/green]")

            # Restore playlists database
            if (
                metadata.get("items", {}).get("playlists")
                and (temp_dir / "playlists.db").exists()
            ):
                time.sleep(0.5)  # Give time for connections to close
                shutil.copy(temp_dir / "playlists.db", _path_manager.saved_playlists)
                console.print("[green]✓ Playlist database restored[/green]")

            # Restore cache if it was backed up
            if metadata.get("items", {}).get("cache"):
                for cache_file in ["cache.db", "lyrics_cache.db"]:
                    if (temp_dir / cache_file).exists():
                        time.sleep(0.5)  # Give time for connections to close
                        shutil.copy(
                            temp_dir / cache_file,
                            _path_manager.construct_path(cache_file),
                        )
                console.print("[green]✓ Cache restored[/green]")

            # Restore downloaded playlists
            playlists_path = temp_dir / "playlists"
            if playlists_path.exists():
                for item in playlists_path.iterdir():
                    if item.is_dir():
                        target_dir = _path_manager.playlists_dir / item.name
                        target_dir.mkdir(parents=True, exist_ok=True)
                        for song_file in item.iterdir():
                            shutil.copy(song_file, target_dir / song_file.name)
                console.print("[green]✓ Downloaded playlists restored[/green]")

            console.print(
                "[bold green]Restoration completed successfully![/bold green]"
            )
            return True

        except Exception as e:
            console.print(f"[red]Error during restoration: {e}[/red]")
            return False
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def list_available_backups(self):
        """List all available backups with their timestamps."""
        backup_files = sorted(
            [f for f in self.backup_dir.glob("aurras_backup_*.zip")],
            key=os.path.getmtime,
            reverse=True,
        )

        if not backup_files:
            console.print("[yellow]No backup files found.[/yellow]")
            return []

        backups = []
        for i, backup_file in enumerate(backup_files, 1):
            try:
                # Try to read metadata for more info
                with zipfile.ZipFile(backup_file, "r") as zipf:
                    try:
                        metadata = json.loads(zipf.read("metadata.json"))
                        date_str = metadata.get("date", "Unknown date")
                        items = ", ".join(metadata.get("items", {}).keys())
                    except:
                        # If metadata can't be read, use file info
                        date_str = datetime.fromtimestamp(
                            os.path.getmtime(backup_file)
                        ).isoformat()
                        items = "Unknown contents"

                size_mb = backup_file.stat().st_size / (1024 * 1024)
                backups.append(
                    {
                        "index": i,
                        "file": backup_file,
                        "date": date_str,
                        "items": items,
                        "size_mb": f"{size_mb:.1f} MB",
                    }
                )
                console.print(
                    f"[cyan]{i}.[/cyan] {backup_file.name} [{date_str}] - {items} - {size_mb:.1f} MB"
                )
            except Exception as e:
                console.print(
                    f"[yellow]Error reading backup {backup_file.name}: {e}[/yellow]"
                )

        return backups
