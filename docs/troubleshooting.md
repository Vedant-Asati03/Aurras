# Aurras Troubleshooting Guide

This guide provides solutions for common issues you might encounter while using Aurras Music Player.

## Installation Issues

### Missing Dependencies

**Symptoms:** Error messages about missing packages, failed imports, or features not working.

**Solution:** Ensure all required dependencies are installed:

```bash
pip install -r requirements.txt
pip install -e . --upgrade  # If installed in development mode
```

For optional dependencies:
```bash
python setup_dependencies.py --optional
```

### External Tools Not Found

**Symptoms:** Errors about MPV or FFmpeg not being found.

**Solution:** Install the required external tools:

```bash
# Debian/Ubuntu
sudo apt install mpv ffmpeg

# Arch Linux
sudo pacman -S mpv ffmpeg

# macOS
brew install mpv ffmpeg

# Windows
choco install mpv ffmpeg
```

## Playback Issues

### No Sound During Playback

**Symptoms:** Progress bar moves but no audio plays.

**Solutions:**
1. Check system volume and ensure speakers/headphones are connected
2. Check if MPV works outside Aurras: `mpv --no-config some_audio_file.mp3`
3. Verify audio drivers are working properly

### Songs Skip Immediately or Fail to Play

**Symptoms:** Songs skip without playing, error messages appear during playback.

**Solutions:**
1. Check your internet connection
2. Try playing a different song to rule out song-specific issues
3. Run `cleanup_cache` to clear cached data that might be corrupted
4. If using offline mode, verify the song files exist in the download directory

### Playback Controls Not Working

**Symptoms:** Keyboard controls like pause, skip, etc. don't respond.

**Solutions:**
1. Make sure you're focused on the terminal window
2. Check if your terminal supports keyboard input capture
3. Try reinstalling MPV with `mpv --vo=null --ao=null` to test if it's an MPV issue

## Spotify Integration Issues

### Authentication Failures

**Symptoms:** "Invalid client", "Invalid redirect URI", or "Authentication failed" errors.

**Solutions:**
1. Verify your Client ID and Secret are correct
2. Check the Redirect URI in your Spotify app settings is *exactly* `http://localhost:8080`
3. Try the manual authentication process described in [Spotify Integration Guide](spotify_integration.md)
4. Run the standalone helper script: `python /home/vedant/.aurras/services/spotify/auth_helper.py`

### No Playlists Found

**Symptoms:** Successfully authenticate but no playlists appear.

**Solutions:**
1. Make sure you have created playlists in your Spotify account
2. Verify the playlists are not private or have special access restrictions
3. Try logging out and back in to your Spotify account in a browser

### Import Failures

**Symptoms:** Authentication works but playlist import fails.

**Solutions:**
1. Check that your internet connection is stable
2. Verify Aurras has write permissions for its database directory
3. Try importing a smaller playlist first to test the process

## Download Issues

### Songs Fail to Download

**Symptoms:** Error messages during download, incomplete downloads, or missing files.

**Solutions:**
1. Check your internet connection
2. Run `pip install --upgrade spotdl` to ensure you have the latest version
3. Verify you have enough disk space
4. Check write permissions for the download directory
5. Try downloading a different song to isolate the issue

### Downloaded Songs Won't Play

**Symptoms:** Offline songs skip or produce errors when played.

**Solutions:**
1. Verify the song files exist and aren't corrupted
2. Check you have the correct codecs installed
3. Try downloading the song again
4. Ensure MPV can play the file format (try playing directly with MPV)

## Database Issues

### Playlists Not Saving

**Symptoms:** Playlists disappear after restart or can't be created.

**Solutions:**
1. Check if the database directory exists and is writable
2. Run `ls -la ~/.aurras/database/` to verify permissions
3. Try creating a backup with the command palette to see if database access works

### Database Errors

**Symptoms:** SQLite errors, database locked messages.

**Solutions:**
1. Close any other instances of Aurras that might be using the database
2. Check if the directory has proper permissions
3. Try restoring from a backup using the command palette

## Cache and Performance Issues

### Slow Performance

**Symptoms:** Commands take a long time to execute, interface feels sluggish.

**Solutions:**
1. Run `cleanup_cache` to remove old cached data
2. Check disk space with `df -h`
3. Close other resource-intensive applications
4. Verify your Python environment isn't overloaded with background processes

### Excessive Disk Usage

**Symptoms:** Aurras is using too much storage space.

**Solutions:**
1. Use `cache_info` to see how much cache is being stored
2. Run `cleanup_cache` with a smaller number of days to keep (e.g., `cleanup_cache 7`)
3. Delete old downloaded songs that you no longer need
4. Configure automatic cache cleanup through the command palette

## Command and Feature Issues

### Commands Not Found

**Symptoms:** "Unknown command" or command not recognized errors.

**Solutions:**
1. Use `?` or `help` to see available commands
2. Check for typos in your command
3. Make sure you're using the correct command format (e.g., for shortcuts)
4. Update Aurras to the latest version

### Features Not Working

**Symptoms:** Features mentioned in documentation aren't available.

**Solutions:**
1. Check if the feature requires optional dependencies
2. Run `setup_dependencies.py --optional` to install all optional features
3. Verify your Aurras version supports the feature
4. Look for error messages in the console output

## Lyrics Issues

### No Lyrics Displayed

**Symptoms:** Songs play but no lyrics appear.

**Solutions:**
1. Check if lyrics display is enabled with `toggle_lyrics`
2. Not all songs have available lyrics - try a popular song as a test
3. Verify you have the `lyrics_extractor` package installed
4. Check your internet connection as lyrics are fetched online

### Translation Not Working

**Symptoms:** Pressing 't' during playback doesn't translate lyrics.

**Solutions:**
1. Make sure you have the `googletrans` package installed
2. Verify lyrics are displayed before attempting translation
3. Check your internet connection
4. Try a different song to test if it's song-specific

## General Troubleshooting Steps

If you encounter any other issues not listed above:

1. **Check Logs**: Examine logs in `~/.aurras/logs/` for error messages
2. **Update Aurras**: Make sure you're using the latest version
3. **Reinstall Dependencies**: Try reinstalling dependencies with:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```
4. **Reset Settings**: Try renaming or removing the settings file to reset to defaults:
   ```bash
   mv ~/.aurras/config/settings.yaml ~/.aurras/config/settings.yaml.bak
   ```
5. **Create a Backup**: Before making major changes, create a backup using the command palette

## Still Having Issues?

If you continue to experience problems not addressed in this guide:

1. Report the issue on our [GitHub Issues Page](https://github.com/vedant-asati03/Aurras/issues)
2. Include error messages, steps to reproduce, and your environment details
