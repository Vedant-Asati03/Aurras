"""
Playlist
"""

import json
import os
import shutil
import subprocess
import sys
from platform import system
from time import sleep
import time
from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion
import yt_dlp

import spotipy
from pick import pick
from requests import get
from rich.console import Console
from rich.table import Table
from rich.text import Text
from spotdl import __main__ as spotdl
from spotipy import util

from authenticatespotify import authenticate_spotify
from playsong import play_playlist_offline, play_song_online

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
                ".aurras",
                "Playlists",
            )
        )

    except FileExistsError:
        pass

    for song in song_names:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
                os.path.expanduser("~"), ".aurras", "Playlists", playlist_name + ".txt"
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
            download_playlist(playlist_name + ".txt")
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

    match choose_playlist:
        case "D":
            play_playlist_offline()

        case "S":
            playlist_dir = os.path.join(os.path.expanduser("~"), ".aurras", "Playlists")
            playlist, _ = pick(
                os.listdir(playlist_dir),
                title="Your Saved Playlists\n\n",
                indicator="⨀",
            )
            subprocess.call(CLRSRC, shell=True)

            with open(
                os.path.join(playlist_dir, playlist),
                "r",
                encoding="UTF-8",
            ) as songs_inplaylist:

                class SONG(Completer):
                    """
                    Shows songs in the playlist
                    """

                    def get_completions(self, document, complete_event):
                        completions = [
                            Completion(recommendation, start_position=0)
                            for recommendation in songs_inplaylist.readlines()
                        ]
                        return completions

                song = prompt(
                    "Search song: ",
                    completer=SONG(),
                    complete_while_typing=True,
                    mouse_support=True,
                    clipboard=True,
                ).strip()

            with open(
                os.path.join(playlist_dir, playlist),
                "r",
                encoding="UTF-8",
            ) as songs_inplaylist:
                index_ofsong = (songs_inplaylist.readlines()).index(song)

            with open(
                os.path.join(playlist_dir, playlist),
                "r",
                encoding="UTF-8",
            ) as songs_inplaylist:
                for song in (songs_inplaylist.readlines())[index_ofsong:]:
                    song = song.replace("\n", "")

                    play_song_online(song)
                    subprocess.call(CLRSRC, shell=True)


def delete_playlist():
    """
    Deletes a playlist
    """

    playlists = pick(
        options=os.listdir(
            os.path.join(os.path.expanduser("~"), ".aurras", "Playlists")
        ),
        multiselect=True,
        title="Your Playlists\n\n",
        min_selection_count=1,
        indicator="⨀",
    )

    removed_playlist = []

    for playlist, _ in playlists:
        os.remove(
            os.path.join(os.path.expanduser("~"), ".aurras", "Playlists", playlist)
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

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                get(song, timeout=20)
            except:
                audio = ydl.extract_info(f"ytsearch:{song}", download=False)["entries"][
                    0
                ]
            else:
                audio = ydl.extract_info(song, download=False)

        with open(
            os.path.join(
                os.path.expanduser("~"), ".aurras", "Playlists", playlist_name
            ),
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
    with open(
        os.path.join(os.path.expanduser("~"), ".aurras", "Playlists", playlist_name),
        "r",
        encoding="UTF-8",
    ) as songs_inplaylist:
        songs = pick(
            options=songs_inplaylist.readlines(),
            title="Select Song[s] to remove",
            multiselect=True,
            indicator="⨀",
        )

    with open(
        os.path.join(os.path.expanduser("~"), ".aurras", "Playlists", playlist_name),
        "r",
        encoding="UTF-8",
    ) as songs_inplaylist:
        for song, _ in songs:
            # print(song)
            # print(songs_inplaylist.readlines())
            (songs_inplaylist.readlines()).remove(song)

        # print(songs_inplaylist.readlines())

    sleep(50)


def download_playlist(playlist_name: str):
    """
    Downloads users playlist
    """
    console.print(
        f"Downloading Playlist - {playlist_name.removesuffix('.txt')}\n\n",
        style="#D09CFA",
    )

    with open(
        os.path.join(os.path.expanduser("~"), ".aurras", "Playlists", playlist_name),
        "r",
        encoding="UTF-8",
    ) as playlist_todownload:
        for song in playlist_todownload.readlines():
            song = song.replace("\n", "")

            try:
                os.makedirs(
                    os.path.join(
                        os.path.expanduser("~"),
                        ".aurras",
                        "Downloaded-Playlists",
                        playlist_name.removesuffix(".txt"),
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
                            ".aurras",
                            "Downloaded-Playlists",
                            playlist_name.removesuffix(".txt"),
                        ),
                    )

    console.print("Download complete.", style="#D09CFA")
    sleep(1)


def import_playlist():
    """
    Imports playlist from other platforms
    """

    proceed, _ = pick(
        options=["YES", "NO"],
        title="First you have to Authenticate yourself with Spotify\n\nDo you want to proceed",
        indicator="»",
    )
    clear_src = "cls" if system().lower().startswith("win") else "clear"
    subprocess.call(clear_src, shell=True)

    match proceed:
        case "YES":
            authenticate_spotify()

            with open(
                os.path.join(os.path.expanduser("~"), ".aurras", "spotify_auth.json"),
                "r",
                encoding="UTF-8",
            ) as credential_data:
                credentials = json.load(credential_data)

            token = util.prompt_for_user_token(
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
                scope=credentials["scope"],
                username=credentials["username"],
                redirect_uri=credentials["redirect_uri"],
            )

            SPOTIFY = spotipy.Spotify(auth=token)

            playlists = SPOTIFY.current_user_playlists()

            name_id = {}
            playlists_name = []

            for user_playlist in playlists["items"]:
                playlist_name, playlist_id = (
                    user_playlist["name"],
                    user_playlist["id"],
                )

                name_id[playlist_name] = playlist_id

                playlists_name.append(playlist_name)

            playlist_name, _ = pick(
                options=playlists_name, title="Your Spotify Playlists", indicator="»"
            )

            tracks = SPOTIFY.playlist_items(name_id[playlist_name])

            for track in tracks["items"]:
                # track["track"]["name"]

                try:
                    os.makedirs(
                        os.path.join(
                            os.path.expanduser("~"),
                            ".aurras",
                            "Playlists",
                        )
                    )

                except FileExistsError:
                    pass

                with open(
                    os.path.join(
                        os.path.expanduser("~"),
                        ".aurras",
                        "Playlists",
                        playlist_name + ".txt",
                    ),
                    "a",
                    encoding="UTF-8",
                ) as playlist_songs:
                    playlist_songs.write(track["track"]["name"] + "\n")
            console.print(f"Created Playlist named - {playlist_name}", style="#D09CFA")
            ask_user = (
                console.input(
                    Text(
                        "Do you want to download this playlist [Y]\n",
                        style="#D09CFA",
                    )
                )
                .strip()
                .capitalize()
            )
            subprocess.call(clear_src, shell=True)
            match ask_user:
                case "Y":
                    download_playlist(playlist_name + ".txt")
                case _:
                    pass

            sleep(1.55)

        case "NO":
            pass

        case _:
            pass
