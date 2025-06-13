# Spotify Integration Guide

This guide explains how to set up and use Aurras' Spotify integration to import your playlists and access your Spotify library through the command-line interface.

## Overview

Aurras provides seamless Spotify integration with secure OAuth authentication and comprehensive playlist import capabilities:

- **CLI-First Design**: All functionality accessible through simple commands
- **Secure Setup**: Interactive credential configuration with automatic setup detection
- **OAuth Authentication**: Industry-standard OAuth with automatic token refresh
- **Complete Library Import**: Import all playlists with full metadata preservation
- **Status Management**: Easy verification, credential management, and reset capabilities

## Quick Setup Commands

Get started with Spotify integration in just a few commands:

```bash
# Set up Spotify integration
aurras setup --spotify

# Check integration status
aurras setup --spotify --status

# Import all your Spotify playlists
aurras playlist --import

# Play an imported playlist
aurras playlist "My Playlist Name"
```

## Setting Up Spotify API Credentials

Before using Spotify integration, you need to create a Spotify app and configure API credentials:

### Step 1: Create Spotify App

1. Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"CREATE APP"**
4. Fill in the app details:
   - **App name**: "Aurras Music Player" (or any name you prefer)
   - **App description**: "Music player app"
   - **Website**: Leave blank or add your preferred URL
   - **Redirect URI**: `http://127.0.0.1:8080` *(must be exact)*
5. Check the agreement checkbox and click **"CREATE"**
6. Copy your **Client ID** from the app dashboard
7. Click **"SHOW CLIENT SECRET"** and copy the **Client Secret**

### Step 2: Configure Aurras

Run the interactive setup command:

```bash
aurras setup --spotify
```

The setup wizard will:

- Display detailed setup instructions
- Prompt for your Client ID and Client Secret
- Guide you through OAuth authentication
- Automatically handle token management
- Confirm successful configuration

## Importing Playlists

```bash
# Import all your Spotify playlists
aurras playlist --import
```

If Spotify isn't configured yet, the import command will automatically guide you through the setup process.

### After Import

Once imported, you can use your Spotify playlists with any Aurras command:

```bash
# Play an imported playlist
aurras playlist "My Spotify Playlist"

# View playlist contents
aurras playlist --list

# Download playlist for offline use
aurras playlist "My Playlist" --download
```

## Managing Your Spotify Integration

### Check Status

```bash
# Check if Spotify is configured and working
aurras setup --spotify --status
```

This command will:

- Verify credential configuration
- Test connection to Spotify API
- Display connected user information
- Report any connection issues

### Reset Credentials

```bash
# Reset and start over with fresh credentials
aurras setup --spotify --reset
```

Use this when you need to change Spotify accounts, fix authentication issues, or start fresh after errors.

## Troubleshooting

### Setup Issues

#### "Invalid redirect URI" Error

Ensure your Spotify app has **exactly** `http://127.0.0.1:8080` as the redirect URI (no trailing slash, all lowercase).

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Select your app → **"EDIT SETTINGS"** → "Redirect URIs"
3. Add: `http://127.0.0.1:8080`
4. Click **"ADD"** then **"SAVE"**

#### "Invalid credentials" or Connection Failed

- Verify Client ID and Secret in your Spotify Developer Dashboard
- Check internet connection
- Reset and try again: `aurras setup --spotify --reset`

### Import Issues

#### "No playlists found" or Import Interrupted

- Ensure you have playlists in your Spotify account
- Check connection: `aurras setup --spotify --status`
- For interrupted imports, run `aurras playlist --import` again (skips already imported playlists)

#### Authentication Problems

- **Browser not opening**: Check default browser settings
- **Token expired**: Run `aurras setup --spotify --reset` and setup again

### Quick Fixes

Most issues can be resolved by resetting credentials:

```bash
aurras setup --spotify --reset
aurras setup --spotify
```

## Technical Details

### Authentication & Storage

- **OAuth 2.0**: Secure authentication with automatic token refresh
- **Credentials**: Stored locally in `~/.aurras/credentials/credentials.json`
- **Playlists**: Imported to local database for offline access
- **Privacy**: No data collection - everything stays on your device

## Quick Reference

| Command                           | Description              |
| --------------------------------- | ------------------------ |
| `aurras setup --spotify`          | Interactive setup wizard |
| `aurras setup --spotify --status` | Check connection status  |
| `aurras setup --spotify --reset`  | Reset credentials        |
| `aurras playlist --import`        | Import all playlists     |
| `aurras playlist "name"`          | Play specific playlist   |
| `aurras playlist --list`          | List all playlists       |

**Need help?** Use `aurras --help` or visit [GitHub Issues](https://github.com/vedant-asati03/Aurras/issues) for support.
