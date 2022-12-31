"""
Plays Song
"""

import os

from requests import get
from rich.console import Console
from youtube_dl import YoutubeDL
from lyrics import show_lyrics


console = Console()


def play_song(song_name: str):
    """
    Searches for song
    """

    ydl_opts = {
        "format": "bestaudio",
        "noplaylist": "True",
        "skipdownload": "True",
        "quiet": "True",
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            get(song_name, timeout=20)
        except:
            audio = ydl.extract_info(f"ytsearch:{song_name}", download=False)[
                "entries"
            ][0]
        else:
            audio = ydl.extract_info(song_name, download=False)

    song_title = audio["title"]
    song_url = audio["webpage_url"]

    console.print(f"Playing🎶: {song_title}\n", end="\r", style="u #E8F3D6")
    show_lyrics(song_title)
    os.system("mpv " + song_url)
