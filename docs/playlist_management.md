# Playlist Management Guide

This guide explains how to create, manage, and use playlists in Aurras Music Player.

## Creating Playlists

Playlists are created automatically when you add songs to them. If a playlist doesn't exist, it will be created when you first add a song.

### Adding Songs to a New or Existing Playlist

Use the `add_song_to_playlist` command or the `aps` shortcut:

```shell
add_song_to_playlist "My Playlist" "Song Title"
aps "My Playlist" "Song Title"
```

## Managing Playlists

You can rename, delete, and view playlists using the following commands:

### Renaming a Playlist

Use the `rename_playlist` command:

```shell
rename_playlist "Old Playlist Name" "New Playlist Name"
```

### Deleting a Playlist

Use the `delete_playlist` command:

```shell
delete_playlist "Playlist Name"
```

### Viewing Playlists

Use the `view_playlists` command:

```shell
view_playlists
```

## Troubleshooting

If you encounter issues with playlists, try the following steps:

1. Ensure you are using the correct command syntax.
2. Check if the playlist or song names contain special characters that might cause issues.
3. Restart the Aurras Music Player application.
4. Consult the Aurras Music Player documentation for more detailed troubleshooting steps.

If the problem persists, contact Aurras Music Player support for further assistance.

