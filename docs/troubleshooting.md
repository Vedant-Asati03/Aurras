# Aurras Troubleshooting Guide

This guide provides solutions for common issues you might encounter while using Aurras.

## Important Tip

**Create a Backup**: Before making any significant changes, always remember to create a backup of your data. This can save you a lot of hassle!

## Installation Issues

### Missing Dependencies

**<u>Symptoms:</u>** You might see error messages indicating missing packages, failed imports, or features that simply aren't working as expected.

**<u>Solutions:</u>**

For **package manager installations** (pip, homebrew, chocolatey, AUR), try upgrading Aurras using your respective package manager:

```bash
# Via pip
pip install --upgrade aurras

# Via Homebrew
brew upgrade aurras

# Via Chocolatey 
choco upgrade aurras

# For AUR users, yay or any other AUR helper
yay -S aurras
```

For **development installations**, ensure your environment is properly initialized:

```bash
python setup_dev_env.py    # Run this to initialize development environment

# then activate the environment as per setup instructions.
```

### External Tools Not Found

**<u>Symptoms:</u>** Errors about MPV or FFmpeg not being found.

- Windows: This error often appears when Aurras can't find libmpv. You might see an error like this:
![libmpv error image](/assets/libmpv_not_found_error.png)

   **<u>Fix:</u>** The simplest solution is to reinstall Aurras. This will not affect your data

- macOS/Linux: This issue is quite rare on these operating systems.

   **<u>Fix:</u>** Simply install MPV using your system's package manager.

## Spotify Integration Issues

### Authentication Failures

**<u>Symptoms:</u>** You might encounter errors such as "Invalid client," "Invalid redirect URI," or "Authentication failed."

**<u>Solutions:</u>**

1. **Verify your Client ID and Secret:** Double-check that these credentials are precisely correct in your Aurras settings.
2. **Check the Redirect URI:** Ensure the Redirect URI configured in your Spotify app settings is exactly `http://127.0.0.1:8080`. Even a slight mismatch can cause issues.
3. **Check your connection status:** Run `aurras setup --spotify --status` to diagnose the connection.

## Download Issues

### Songs Fail to Download

**<u>Symptoms:</u>** You may see error messages during the download process, incomplete downloads, or missing files after a download attempt. If the error mentions `ffmpeg not found`, try installing it via your package manager.

If error says `ffmpeg not found`, try installing it using your package manager

**<u>Solutions:</u>**

1. **Check your internet connection:** A stable connection is crucial for downloads.
2. **Update `spotdl`:** Run `pip install --upgrade spotdl` to ensure you have the latest version of the downloading utility.
3. **Verify disk space:** Make sure you have sufficient free disk space on your device.
4. **Check write permissions:** Ensure Aurras has the necessary permissions to write files to your chosen download directory.
5. **Try a different song:** Download a different, popular song to determine if the issue is specific to the song or a broader problem.

## Database Issues

### Playlists Not Saving

**<u>Symptoms:</u>** Your playlists might disappear after restarting Aurras, or you may be unable to create new ones.

**<u>Solutions:</u>**

1. Check if the database directory exists and is writable
2. Run `ls -la ~/.aurras/database/` to verify permissions

### Database Errors

**<u>Symptoms:</u>** SQLite errors, "database locked" messages.

**<u>Solutions:</u>**

1. Close any other instances of Aurras that might be using the database
2. Check if the directory has proper permissions
3. Try restoring from a backup

## Cache and Performance Issues

### Slow Performance

**<u>Symptoms:</u>** Commands take a long time to execute, interface feels sluggish.

**<u>Solutions:</u>**

1. **Clean up old cache:** Run `cleanup_cache` to remove cached data older than 30 days. This can significantly improve performance.
2. Close other resource-intensive applications

### Excessive Disk Usage

**<u>Symptoms:</u>** Aurras is using too much storage space.

**<u>Solutions:</u>**

1. Use `cache_info` to see how much cache is being stored
2. Run `cleanup_cache` with a smaller number of days to keep (e.g., `cleanup_cache 7`)
3. Delete old downloaded songs that you no longer need

## Command and Feature Issues

### Commands Not Found

**<u>Symptoms:</u>** "Unknown command" or command not recognized errors.

**<u>Solutions:</u>**

1. Type `help` to see available commands
2. Check for typos in your command

## Lyrics Issues

### No Lyrics Displayed

**<u>Symptoms:</u>** Songs play but no lyrics appear.

**<u>Solutions:</u>**

1. Check if lyrics display is enabled with `lyrics`(Interactive mode) or `aurras settings --set appearance-settings.display-lyrics yes`(Command line mode)
2. Not all songs have available lyrics - try a popular song as a test
3. Verify you have the `synced-lyrics` package installed
4. Check your internet connection as lyrics are fetched online

## General Troubleshooting Steps

If you encounter any other issues not listed above:

1. **Check Logs**: Examine logs in `~/.aurras/logs/` for error messages
2. **Update Aurras**: Make sure you're using the latest version
3. **Reinstall Aurras**: Try reinstalling aurras with:

   ```bash
   # via pip
   pip install --upgrade aurras

   # via homebrew
   brew upgrade aurras

   # via chocolatey 
   choco upgrade aurras

   # For AUR users, yay or any other AUR helper
   yay -S aurras
   ```

## Still Having Issues?

If you continue to experience problems not addressed in this guide, please don't hesitate to report the issue:

1. **Report on GitHub:** Visit our [GitHub Issues Page](https://github.com/vedant-asati03/Aurras/issues) to create a new issue.
2. **Provide details:** When reporting, please include all relevant error messages, clear steps to reproduce the issue, and details about your operating system and environment.
