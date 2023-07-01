"""
Plays Song
"""

import os
import platform
import threading
import subprocess
from platform import system

import yt_dlp
from pick import pick
from requests import get
from rich.console import Console

from lyrics import show_lyrics, translate_lyrics
from logger import debug_log
from mpvsetup import mpv_setup

console = Console()
CLRSRC = "cls" if system().lower().startswith("win") else "clear"
WINDOWS = platform.system() == "Windows"

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

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            get(song_name, timeout=15)
        except Exception:
            audio = ydl.extract_info(f"ytsearch:{song_name}", download=False)[
                "entries"
            ][0]
        else:
            audio = ydl.extract_info(song_name, download=False)

    song_title = audio["title"]
    song_url = audio["webpage_url"]

    console.print(f"Playing🎶: {song_title}\n", end="\r", style="u #E8F3D6")

    event = threading.Event()

    lyrics_translation = threading.Thread(
        target=translate_lyrics,
        args=(
            song_name,
            song_title,
            event,
        ),
    )

    show_lyrics(song_title)

    lyrics_translation.start()

    subprocess.run(
        (f"mpv --include={conf_file} --input-conf={input_file} {song_url}"),
        shell=True,
        check=True,
    )
    event.set()

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
        command = [
            "mpv",
            f"--include={conf_file}",
            f"--input-conf={input_file}",
            os.path.join(
                os.path.expanduser("~"),
                ".aurras",
                "Songs",
                song,
            ),
        ]
        debug_log(f"playing offline song with command: {command}")
        subprocess.run(
            command,
            shell=True if WINDOWS else False,
            check=True,
        )

        # subprocess.call(CLRSRC, shell=True)


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
            shell=True if WINDOWS else False,
            check=True,
        )

        subprocess.call(CLRSRC, shell=True)


if __name__ == "__main__":
    play_song_offline()
