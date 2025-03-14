import aiosqlite

from config import path
from src.scripts.playlist.import_playlist.import_from_spotify import (
    ImportSpotifyPlaylist,
)


class ActivePlaylistSync:
    def __init__(self) -> None:
        self.import_from_spotify = ImportSpotifyPlaylist()
        self.saved_playlists = None
        self.imported_playlists = None

    async def _get_saved_playlists_from_db(self):
        async with aiosqlite.connect(path.saved_playlists) as imported_playlists:
            cursor = await imported_playlists.cursor()

            await cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

            list_of_tupled_playlists = await cursor.fetchall()
            self.saved_playlists = {
                playlist[0] for playlist in list_of_tupled_playlists
            }

    async def _get_imported_playlists_saved_in_db(self):
        await self._get_saved_playlists_from_db()

        user_spotify_playlists = {
            my_playlist["name"]
            for my_playlist in self.import_from_spotify.spotify_user_playlists["items"]
        }

        self.imported_playlists = list(self.saved_playlists & user_spotify_playlists)

    async def update_imported_playlists(self):
        await self._get_imported_playlists_saved_in_db()

        for playlist in self.imported_playlists:
            await self.import_from_spotify._track_spotify_playlist(playlist)
            await self.import_from_spotify._save_playlist_to_db(playlist)
