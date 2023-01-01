"""
Plays Song
"""

import os
import subprocess

from platform import system
from requests import get
from rich.console import Console
from youtube_dl import YoutubeDL

from lyrics import show_lyrics
from mpvsetup import mpv_setup


console = Console()
CLRSRC = "cls" if system().lower().startswith("win") else "clear"


def play_song(song_name: str):
    """
    Searches for song
    """

    mpv_setup()

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

    conf_file = os.path.join(os.path.expanduser("~"), ".aurras", "mpv", "mpv.conf")
    input_file = os.path.join(os.path.expanduser("~"), ".aurras", "mpv", "input.conf")

    console.print(f"Playing🎶: {song_title}\n", end="\r", style="u #E8F3D6")
    show_lyrics(song_title)

    subprocess.run(
        (f"mpv --include={conf_file} --input-conf={input_file} {song_url}"), shell=True
    )

    subprocess.call(CLRSRC, shell=True)
