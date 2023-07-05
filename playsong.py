"""
Plays Song
"""

import os
import random
import platform
import threading
import subprocess

import yt_dlp

from pick import pick
from requests import get
from pytube import Playlist
from logger import debug_log
from rich.console import Console
from prompt_toolkit import prompt

from mpvsetup import mpv_setup
from term_utils import clear_screen
from recommendation import recommend_songs
from lyrics import show_lyrics, translate_lyrics


console = Console()
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

    clear_screen()


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
    clear_screen()

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
        recommend_songs(song)

        clear_screen()


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
    clear_screen()

    song = prompt(
        completer=(os.listdir(os.path.join(path, playlist))),
        complete_while_typing=True,
        mouse_support=True,
        clipboard=True,
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
        recommend_songs(song)

        clear_screen()


def shuffle_play(stop_playing_event):
    """
    #!Plays songs from recommendations(If recommend_songs.txt exists), else play songs randomly
    """

    while not stop_playing_event.is_set():
        if os.path.exists(
            os.path.join(os.path.expanduser("~"), ".aurras", "recommended_songs.txt")
        ):
            with open(
                os.path.join(
                    os.path.expanduser("~"), ".aurras", "recommended_songs.txt"
                ),
                "r",
                encoding="UTF-8",
            ) as recommended_list:
                reader = recommended_list.readlines()
                random.shuffle(reader)

            for song in reader:
                if stop_playing_event.is_set():
                    break
                play_song_online(song)

        else:
            playlist_link = [
                "https://music.youtube.com/playlist?list=RDCLAK5uy_ksEjgm3H_7zOJ_RHzRjN1wY-_FFcs7aAU&feature=share&playnext=1",
                "https://music.youtube.com/playlist?list=RDCLAK5uy_n9Fbdw7e6ap-98_A-8JYBmPv64v-Uaq1g&feature=share&playnext=1",
                "https://music.youtube.com/playlist?list=RDCLAK5uy_n9Fbdw7e6ap-98_A-8JYBmPv64v-Uaq1g&feature=share&playnext=1",
                "https://www.youtube.com/playlist?list=PL6k9a6aYB2zk0qSbXR-ZEiwqgdHymsRtQ",
                "https://www.youtube.com/playlist?list=PLO7-VO1D0_6NmK47v6tpOcxurcxdW-hZa",
                "https://www.youtube.com/playlist?list=PL9bw4S5ePsEEqCMJSiYZ-KTtEjzVy0YvK",
            ]

            random.shuffle(playlist_link)

            top_song = Playlist(random.choice(playlist_link)).video_urls

            song = random.choice(top_song)
            if stop_playing_event.is_set():
                break
            play_song_online(song)


if __name__ == "__main__":
    play_song_offline()
