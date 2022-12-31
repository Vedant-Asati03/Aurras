"""
Playlist
"""

import os
import sys
import shutil
import subprocess

from time import sleep
from platform import system

from pick import pick
from requests import get
from youtube_dl import YoutubeDL
from rich.console import Console
from rich.text import Text
from rich.table import Table
from spotdl import __main__ as spotdl

from lyrics import show_lyrics


console = Console()
CLRSRC = "cls" if system().lower().startswith("win") else "clear"
table = Table(show_header=False, header_style="bold magenta")


def create_playlist(playlist_name: str, song_names: str):
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

    for song in song_names:

        with YoutubeDL(ydl_opts) as ydl:
            try:
                get(song_names, timeout=20)
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
    console.print(f"Created Playlist named - {playlist_name}", style="#D09CFA")
    ask_user = (
        console.input(
            Text("Do you want to download this playlist [Y]\n", style="#D09CFA")
        )
        .strip()
        .capitalize()
    )
    subprocess.call(CLRSRC, shell=True)

    match ask_user:

        case "Y":
            download_playlist(playlist_name+".txt")
        case _:
            pass

    sleep(1.55)


def play_playlist():
    """
    Shows all the songs in a playlist
    """
    choose_playlist = (
        console.input(Text("DOWNLOADED-PLAYLISTS[D] | SAVED-PLAYLISTS[S]\n"))
        .strip()
        .capitalize()
    )

    ydl_opts = {
        "format": "bestaudio",
        "noplaylist": "True",
        "skipdownload": "True",
        "quiet": "True",
    }

    match choose_playlist:

        case "D":

            path = os.path.join(
                os.path.expanduser("~"), "AURRAS", "DOWNLAODED-PLAYLISTS"
            )
            playlist, _ = pick(
                os.listdir(path),
                title="Your Downloaded Playlists\n\n",
                indicator=">",
            )
            subprocess.call(CLRSRC, shell=True)

            song, _ = pick(
                options=os.listdir(os.path.join(path, playlist)),
                title="Select a song to play",
            )

            index_ofsong = (os.listdir(os.path.join(path, playlist))).index(song)
            for song in (os.listdir(os.path.join(path, playlist)))[index_ofsong:]:

                with YoutubeDL(ydl_opts) as ydl:
                    try:
                        get(song, timeout=20)
                    except:
                        audio = ydl.extract_info(f"ytsearch:{song}", download=False)[
                            "entries"
                        ][0]
                    else:
                        audio = ydl.extract_info(song, download=False)

                song_title = audio["title"]
                song_url = audio["webpage_url"]

                console.print(f"Playing🎶: {song_title}\n", end="\r", style="u #E8F3D6")
                show_lyrics(song_title)
                os.system("mpv " + song_url)
                subprocess.call(CLRSRC, shell=True)

        case "S":

            path = os.path.join(os.path.expanduser("~"), "AURRAS", "PLAYLISTS")
            playlist, _ = pick(
                os.listdir(path),
                title="Your Saved Playlists\n\n",
                indicator=">",
            )
            subprocess.call(CLRSRC, shell=True)

            with open(
                os.path.join(path, playlist),
                "r",
                encoding="UTF-8",
            ) as songs_inplaylist:
                song, _ = pick(
                    options=songs_inplaylist.readlines(), title="Select a song to play"
                )

            with open(
                os.path.join(path, playlist),
                "r",
                encoding="UTF-8",
            ) as songs_inplaylist:
                index_ofsong = (songs_inplaylist.readlines()).index(song)

            with open(
                os.path.join(path, playlist),
                "r",
                encoding="UTF-8",
            ) as songs_inplaylist:
                for song in (songs_inplaylist.readlines())[index_ofsong:]:

                    song = song.replace("\n", "")

                    with YoutubeDL(ydl_opts) as ydl:
                        try:
                            get(song, timeout=20)
                        except:
                            audio = ydl.extract_info(
                                f"ytsearch:{song}", download=False
                            )["entries"][0]
                        else:
                            audio = ydl.extract_info(song, download=False)

                    song_title = audio["title"]
                    song_url = audio["webpage_url"]

                    console.print(
                        f"Playing🎶: {song_title}\n", end="\r", style="u #E8F3D6"
                    )
                    show_lyrics(song_title)
                    os.system("mpv " + song_url)
                    subprocess.call(CLRSRC, shell=True)


def delete_playlist():
    """
    Deletes a playlist
    """

    playlists = pick(
        options=os.listdir(
            os.path.join(os.path.expanduser("~"), "AURRAS", "PLAYLISTS")
        ),
        multiselect=True,
        title="Your Playlists\n\n",
        min_selection_count=1,
    )

    removed_playlist = []

    for playlist, _ in playlists:
        os.remove(
            os.path.join(os.path.expanduser("~"), "AURRAS", "PLAYLISTS", playlist)
        )
        removed_playlist.append(playlist)

    console.print(f"Removed playlist - {removed_playlist}")
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


def remove_fromplaylist(playlist_name: str):
    """
    Removes song from a playlist
    """


def download_playlist(playlist_name: str):
    """
    Downloads users playlist
    """
    console.print(
        f"Downloading Playlist - {playlist_name.removesuffix('.txt')}\n\n",
        style="#D09CFA",
    )

    with open(
        os.path.join(os.path.expanduser("~"), "AURRAS", "PLAYLISTS", playlist_name),
        "r",
        encoding="UTF-8",
    ) as playlist_todownload:

        for song in playlist_todownload.readlines():

            song = song.replace("\n", "")

            try:
                os.makedirs(
                    os.path.join(
                        os.path.expanduser("~"),
                        "AURRAS",
                        "DOWNLOADED-PLAYLISTS",
                        playlist_name,
                    )
                )
            except FileExistsError:
                pass

            subprocess.check_call([sys.executable, spotdl.__file__, song])

            for file in os.listdir():
                if file.endswith(".mp3"):
                    shutil.move(
                        file,
                        os.path.join(
                            os.path.expanduser("~"),
                            "AURRAS",
                            "DOWNLOADED-PLAYLISTS",
                            playlist_name,
                        ),
                    )

    console.print("Download complete.", style="#D09CFA")
