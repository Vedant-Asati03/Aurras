"""
Plays Song
"""

import os
import subprocess

from platform import system
from pick import pick
from requests import get
from rich.console import Console
from youtube_dl import YoutubeDL

from lyrics import show_lyrics
from mpvsetup import mpv_setup


console = Console()
CLRSRC = "cls" if system().lower().startswith("win") else "clear"

conf_file = os.path.join(os.path.expanduser("~"), ".aurras", "mpv", "mpv.conf")
input_file = os.path.join(os.path.expanduser("~"), ".aurras", "mpv", "input.conf")


def play_song_online(song_name: str):
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

    console.print(f"Playing🎶: {song_title}\n", end="\r", style="u #E8F3D6")
    show_lyrics(song_title)

    subprocess.run(
        (f"mpv --include={conf_file} --input-conf={input_file} {song_url}"), shell=True
    )

    subprocess.call(CLRSRC, shell=True)


def play_song_offline():
    """
    Plays songs offline
    """

    mpv_setup()

    path = os.path.join(os.path.expanduser("~"), ".aurras", "Songs")
    song, _ = pick(
        options=os.listdir(os.path.join(path)),
        title="Select a song to play",
    )
    subprocess.call(CLRSRC, shell=True)

    index_ofsong = (os.listdir(os.path.join(path))).index(song)
    for song in (os.listdir(os.path.join(path)))[index_ofsong:]:

        console.print(f"Playing🎶: {song}\n", end="\r", style="u #E8F3D6")
        subprocess.run(
            [
                "mpv",
                f"--include={conf_file}",
                f"--input-conf={input_file}",
                os.path.join(
                    os.path.expanduser("~"),
                    ".aurras",
                    "Songs",
                    song,
                ),
            ],
            shell=True,
        )

        subprocess.call(CLRSRC, shell=True)


def play_playlist_offline():
    """
    Plays playlist offline
    """

    mpv_setup()

    path = os.path.join(os.path.expanduser("~"), ".aurras", "Downloaded-Playlists")
    playlist, _ = pick(
        os.listdir(path),
        title="Your Downloaded Playlists\n\n",
        indicator="⨀",
    )
    subprocess.call(CLRSRC, shell=True)

    song, _ = pick(
        options=os.listdir(os.path.join(path, playlist)),
        title="Select a song to play",
    )

    index_ofsong = (os.listdir(os.path.join(path, playlist))).index(song)
    for song in (os.listdir(os.path.join(path, playlist)))[index_ofsong:]:

        console.print(f"Playing🎶: {song}\n", end="\r", style="u #E8F3D6")
        subprocess.run(
            [
                "mpv",
                f"--include={conf_file}",
                f"--input-conf={input_file}",
                os.path.join(
                    os.path.expanduser("~"),
                    ".aurras",
                    "Downloaded-Playlists",
                    playlist,
                    song,
                ),
            ],
            shell=True,
        )

        subprocess.call(CLRSRC, shell=True)
