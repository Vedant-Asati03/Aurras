import os
import sqlite3

import yt_dlp


def search_song(song_name: str):
    """
    Search the song
    """
    cache_file = os.path.join(os.path.expanduser("~"), ".aurras", "cache.db")
    with sqlite3.connect(cache_file) as cache:

        ydl_opts = {
            "format": "bestaudio",
            "noplaylist": "True",
            "skipdownload": "True",
            "quiet": "True",
            "youtube_skip_dash_manifest": "True",
        }

        cursor = cache.cursor()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS cache (song_name TEXT, song_url TEXT)"""
        )

        cursor.execute("SELECT song_name, song_url FROM cache")

        rows = cursor.fetchall()

        if rows is not None:
            for row in rows:
                if song_name == row[0]:
                    song_url = row[1]
                    return [song_name, song_url]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                audio = ydl.extract_info(f"ytsearch:{song_name}", download=False)[
                    "entries"
                ][0]
            except Exception:
                audio = ydl.extract_info(song_name, download=False)

        song_title = audio["title"]
        song_url = audio["webpage_url"]

        cursor.execute(
            "INSERT INTO cache (song_name, song_url) VALUES (:song_name, :song_url)",
            {"song_name": song_name, "song_url": song_url},
        )

        return [song_title, song_url]
