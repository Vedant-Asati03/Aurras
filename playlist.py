"""
Playlist
"""

import os

from time import sleep
from requests import get
from pick import pick
from youtube_dl import YoutubeDL
from rich.console import Console


console = Console()


def create_playlist(playlist_name: str, song_name: str):
    """
    Creates user playlist
    """
    ydl_opts = {
        "format": "bestaudio",
        "noplaylist": "True",
        "skipdownload": "True",
        "quiet": "True",
    }

    try:
        os.makedirs(
            os.path.join(
                os.path.expanduser("~"),
                "AURRAS",
                "PLAYLISTS",
            )
        )

    except FileExistsError:
        pass

    for song in song_name:

        with YoutubeDL(ydl_opts) as ydl:
            try:
                get(song_name, timeout=20)
            except:
                audio = ydl.extract_info(f"ytsearch:{song}", download=False)["entries"][
                    0
                ]
            else:
                audio = ydl.extract_info(song, download=False)

        with open(
            os.path.join(
                os.path.expanduser("~"), "AURRAS", "PLAYLISTS", playlist_name + ".txt"
            ),
            "a",
            encoding="UTF-8",
        ) as playlist_songs:
            playlist_songs.write(audio["title"] + "\n")
    print(f"Created Playlist named - {playlist_name}")
    sleep(1.55)


def view_playlist():
    """
    Shows all the songs in a playlist
    """
    playlists = os.listdir(os.path.join(os.path.expanduser("~"), "AURRAS", "PLAYLISTS"))
    playlist, _ = pick(playlists)

    return playlist


def delete_playlist(playlist_name: str):
    """
    Deletes a playlist
    """
    os.remove(
        os.path.join(os.path.expanduser("~"), "AURRAS", "PLAYLISTS", playlist_name)
    )
    console.print(f"Removed playlist - {playlist_name}")
    sleep(1.5)


def add_inplaylist(playlist_name: str, song_names: str):
    """
    Adds a song, without deleting any of the content in the playlist
    """

    ydl_opts = {
        "format": "bestaudio",
        "noplaylist": "True",
        "skipdownload": "True",
        "quiet": "True",
    }

    for song in song_names:

        with YoutubeDL(ydl_opts) as ydl:
            try:
                get(song, timeout=20)
            except:
                audio = ydl.extract_info(f"ytsearch:{song}", download=False)["entries"][
                    0
                ]
            else:
                audio = ydl.extract_info(song, download=False)

        with open(
            os.path.join(os.path.expanduser("~"), "AURRAS", "PLAYLISTS", playlist_name),
            "a",
            encoding="UTF-8",
        ) as playlist_songs:
            playlist_songs.write(audio["title"] + "\n")

    console.print(f"Added songs in Playlist - {playlist_name}")
    sleep(1.55)
