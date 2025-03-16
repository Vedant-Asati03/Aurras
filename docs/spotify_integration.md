# Spotify Integration Guide

This guide explains how to set up and use the Spotify integration in Aurras to import your playlists.

## Setting Up Spotify API Credentials

Before you can import playlists from Spotify, you need to set up API credentials:

1. Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "CREATE APP" button
4. Fill in the following details:
   - App name: "Aurras Music Player" (or any name you prefer)
   - App description: "Music player app"
   - Website: You can leave this blank
   - **Redirect URI: `http://localhost:8080`** (this must be EXACTLY as shown)
5. Check the agreement checkbox and click "CREATE"
6. On your app page, note your "Client ID" 
7. Click "SHOW CLIENT SECRET" and note your "Client Secret"

## Configuring in Aurras

1. In Aurras, use the `setup_spotify` command or select "Setup Spotify" from the command palette
2. Enter the Client ID and Client Secret from your Spotify app
3. Follow the authentication prompts when importing playlists

## Importing Playlists

To import playlists from Spotify:

1. Run the `import_playlist` command
2. If this is your first time, you'll need to authorize Aurras:
   - A browser will open to the Spotify authorization page
   - After authorizing, you'll be redirected to a page
   - Copy the **FULL URL** from your browser's address bar (starting with `http://localhost:8080?code=...`)
   - Paste this URL into Aurras when prompted
3. For subsequent imports, authentication will happen automatically using the saved token
4. Select which playlist you want to import from the list that appears
5. Confirm any overwrite prompts if the playlist already exists
6. Wait for the playlist to be imported

## Token Refreshing

Aurras automatically stores and manages your Spotify access tokens:

- The first time you use Spotify features, you'll need to complete the authorization process
- For subsequent uses, Aurras will automatically use the saved token
- If the token expires, Aurras will refresh it without requiring re-authorization
- You will only need to go through the full authorization again if your refresh token expires or becomes invalid (usually after ~60 days of inactivity)

## Common Issues and Solutions

### "Invalid redirect URI" Error

If you see this error, it means the redirect URI in your Spotify app doesn't exactly match what Aurras is using.

**Solution:**
1. Go to your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Select your app
3. Click "EDIT SETTINGS"
4. Under "Redirect URIs", check that you have **EXACTLY** `http://localhost:8080`
   - No trailing slash (not `http://localhost:8080/`)
   - No extra characters
   - Correct capitalization (all lowercase)
5. Click "ADD" then "SAVE"

### "Invalid authorization code" Error

This happens when:
1. The code has expired (waited too long between authorization and submission)
2. You provided the wrong URL (e.g., the original authorization URL instead of the redirect URL)

**Solution:**
- Try the import process again, completing it promptly
- Make sure to copy the URL from your browser AFTER authorization completes

### Authentication Timeouts

If the authentication process seems to hang indefinitely:

**Solution:**
1. Press Ctrl+C to cancel
2. Run the authentication helper script: `python /home/vedant/.aurras/services/spotify/auth_helper.py`
3. Try the import process again

## Manual Authentication

If you continue to have issues with the standard authentication flow:

1. Go to your command palette (`>` or `cmd`)
2. Select "Setup Spotify" to ensure credentials are correct
3. Run the standalone authentication helper: `python /home/vedant/.aurras/services/spotify/auth_helper.py`
4. Once authenticated, run `import_playlist` again

## Removing Stored Authentication

If you want to remove your stored Spotify authentication:

1. Delete the token cache file: `rm ~/.aurras/.cache-spotify`
2. You'll need to go through the full authentication process the next time you use Spotify features
