"""
Playlist
"""

import os
import sys
import shutil
import sqlite3
import subprocess
from time import sleep

import spotipy
from pick import pick
from spotipy import util
from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion

from rich.table import Table
from rich.console import Console
from spotdl import __main__ as spotdl

from searchsong import search_song
from term_utils import clear_screen
from authenticatespotify import authenticate_spotify
from playsong import play_playlist_offline, play_song_online

console = Console()
table = Table(show_header=False, header_style="bold magenta")


def create_playlist(playlist_name: str, song_names: str):
    """
    Creates user playlist
    """

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

    path_playlists = os.path.join(
        os.path.expanduser("~"), ".aurras", "Playlists", playlist_name + ".db"
    )

    for song in song_names:

        with sqlite3.connect(path_playlists) as playlist_songs:

            cursor = playlist_songs.cursor()

            cursor.execute(
                """CREATE TABLE IF NOT EXISTS playlist (id INTEGER PRIMARY KEY, songs TEXT)"""
            )

            cursor.execute(
                "INSERT INTO playlist (songs) VALUES (:song)", {"song": song}
            )

    console.print(f"Created Playlist named - {playlist_name}", style="#D09CFA")

    ask_user, _ = pick(
        title="Do you want to download this playlist",
        options=["Yes, ofcourse", "No"],
        indicator="⁕",
    )
    clear_screen()

    match ask_user:
        case "Yes, ofcourse":
            download_playlist(playlist_name + ".txt")
        case _:
            pass
    sleep(1.55)


def play_playlist():
    """
    Plays the Playlists
    """

    choose_playlist, _ = pick(
        options=["Downloaded Playlists", "Saved Playlists"], indicator="⁕"
    )

    match choose_playlist:
        case "Downloaded Playlists":
            play_playlist_offline()

        case "Saved Playlists":
            path_playlist = os.path.join(
                os.path.expanduser("~"), ".aurras", "playlists.db"
            )

            with sqlite3.connect(os.path.join(path_playlist)) as playlist:

                cursor = playlist.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

                tables = cursor.fetchall()
                table_names = [table[0] for table in tables]

                playlist, _ = pick(
                    options=table_names,
                    title="Your Playlists\n\n",
                    indicator="⁕",
                )

                cursor.execute(f"SELECT playlists_songs FROM '{playlist}'")
                songs = cursor.fetchall()

                class SONG(Completer):
                    """
                    Shows songs in the playlist
                    """

                    def get_completions(self, document, complete_event):
                        completions = [
                            Completion(str(recommendation[0]), start_position=0)
                            for recommendation in songs
                        ]
                        return completions

                song = prompt(
                    placeholder="Search Song",
                    completer=SONG(),
                    complete_while_typing=True,
                    mouse_support=True,
                    clipboard=True,
                ).strip()

                clear_screen()

                cursor.execute(
                    f"SELECT id FROM '{playlist}' WHERE playlists_songs = (:song)",
                    {"song": song},
                )
                result = cursor.fetchone()
                song_index = result[0]

                cursor.execute(
                    f"SELECT playlists_songs FROM '{playlist}' WHERE id >= ?",
                    (song_index,),
                )

                results = cursor.fetchall()
                songs_after = [row[0] for row in results]

                for song in songs_after:
                    play_song_online(song)
                    clear_screen()


def delete_playlist():
    """
    Deletes a playlist
    """

    path_playlists = os.path.join(os.path.expanduser("~"), ".aurras", "playlists.db")

    with sqlite3.connect(path_playlists) as playlist:

        cursor = playlist.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]

        # options = []

        # for table_name in table_names:
        #     options.append(table_name)

        playlists = pick(
            options=table_names,
            multiselect=True,
            title="Your Playlists\n\n",
            indicator="⁕",
        )

        removed_playlists = [playlists]

        for playlist, _ in playlists:
            cursor.execute(f"DROP TABLE IF EXISTS '{playlist}'")

        console.print(f"Removed playlist - {', '.join(removed_playlists)}")
        sleep(1.5)


def add_inplaylist(playlist_name: str, song_names: str):
    """
    Adds a song, without deleting any of the content in the playlist
    """

    for song in song_names:

        with open(
            os.path.join(
                os.path.expanduser("~"), ".aurras", "Playlists", playlist_name
            ),
            "a",
            encoding="UTF-8",
        ) as playlist_songs:
            playlist_songs.write(search_song(song)[0] + "\n")

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
    path_playlist = os.path.join(os.path.expanduser("~"), ".aurras", "playlists.db")
    path_downloadplaylist = os.path.join(
        os.path.expanduser("~"),
        ".aurras",
        "Downloaded-Playlists",
        playlist_name,
    )

    try:
        os.makedirs(path_downloadplaylist)
    except FileExistsError:
        pass

    console.print(
        f"Downloading Playlist - {playlist_name}\n\n",
        style="#D09CFA",
    )

    with sqlite3.connect(path_playlist) as playlist_download:

        cursor = playlist_download.cursor()

        cursor.execute(f"SELECT playlists_songs FROM '{playlist_name}'")
        rows = cursor.fetchall()

        for row in rows:
            for song in row:

                subprocess.check_call([sys.executable, spotdl.__file__, song])

                for file in os.listdir():
                    if file.endswith(".mp3"):
                        shutil.move(file, path_downloadplaylist)

    console.print("Download complete.", style="#D09CFA")
    sleep(1)


def import_playlist():
    """
    Imports playlist from other platforms
    """
    path_authfile = os.path.join(
        os.path.expanduser("~"),
        ".aurras",
        "spotify_auth.db",
    )

    proceed, _ = pick(
        options=["Yeah", "Nope"],
        title="First you have to Authenticate yourself with Spotify\n\nDo you want to proceed",
        indicator="»",
    )
    clear_screen()

    match proceed:
        case "Yeah":
            if not os.path.exists(path_authfile):
                authenticate_spotify()
            else:
                pass

            with sqlite3.connect(path_authfile) as auth:

                cursor = auth.cursor()

                cursor.execute(
                    "SELECT client_id, client_secret, scope, username, redirect_uri FROM spotify_auth"
                )
                row = cursor.fetchone()

                token = util.prompt_for_user_token(
                    client_id=row[0],
                    client_secret=row[1],
                    scope=row[2],
                    username=row[3],
                    redirect_uri=row[4],
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

            path_playlist = os.path.join(
                os.path.expanduser("~"),
                ".aurras",
                "playlists.db",
            )

            with sqlite3.connect(path_playlist) as playlist:
                cursor = playlist.cursor()

                for track in tracks["items"]:
                    # track["track"]["name"]

                    cursor.execute(
                        f"CREATE TABLE IF NOT EXISTS '{playlist_name}' (id INTEGER PRIMARY KEY, playlists_songs TEXT)"
                    )

                    cursor.execute(
                        f"INSERT INTO '{playlist_name}' (playlists_songs) VALUES (:song)",
                        {"song": track["track"]["name"]},
                    )

            console.print(f"Created Playlist - {playlist_name}", style="#D09CFA")

            ask_user, _ = pick(
                title="Do you want to download this Playlist\n\n",
                options=["Nah...", "Yes, why not!"],
                indicator="»",
            )

            clear_screen()
            match ask_user:
                case "Yes, why not!":
                    download_playlist(playlist_name)
                case _:
                    pass

            sleep(1.55)

        case _:
            pass
