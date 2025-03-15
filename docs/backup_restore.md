# Backup and Restore in Aurras

Aurras includes a comprehensive backup and restore system to ensure your data and settings are preserved when you upgrade or reinstall the application.

## Automatic Backups

By default, Aurras will automatically create backups of your:

- Play history
- Playlists
- Settings
- Downloaded content (optional)

These backups are created:
- When triggered by the automatic backup schedule (default: every 7 days)
- When explicitly requested through the Command Palette

## Managing Backups

You can manage the backup system through the Command Palette (press `>` at the main prompt):

### Toggle Backup System
Enable or disable the automatic backup system. When enabled, you can specify how frequently automatic backups should occur.

### Create Manual Backup
Create an immediate backup of your data without waiting for the automatic schedule.

### Restore from Backup
Restore your data from a previously created backup. This will list all available backups with their timestamps and contents, allowing you to choose which one to restore from.

## Backup Configuration

The backup system is configured through the settings file. The following options are available:

- `enabled`: Whether the backup system is active
- `auto-backup`: Whether backups should be created automatically
- `backup-frequency`: How often (in days) automatic backups should occur
- `backup-location`: Where backups should be stored
- `backup-items`: Which items should be included in backups:
  - `history`: Play history
  - `playlists`: Playlists
  - `settings`: Application settings
  - `cache`: Cached data (disabled by default as it can be large)

## Backup Location

By default, backups are stored in the `~/.aurras/backups` directory. You can change this location in the settings file if desired.

## Manual Restoration

In cases where you need to restore Aurras data manually (e.g., after a fresh installation), you can:

1. Install Aurras
2. Copy your backup file to the `~/.aurras/backups` directory
3. Run Aurras and use the "Restore from Backup" option in the Command Palette

This will restore your settings, play history, and playlists from the backup.
