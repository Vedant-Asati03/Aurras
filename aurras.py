"""
Music-Player
"""

import os
import sys
import random
import subprocess
import urllib.request

from time import sleep
from platform import system

from pick import pick
from pytube import Playlist
from rich.text import Text
from rich.console import Console
from rich.table import Table

from downloadsong import download_song
from playsong import play_song_offline, play_song_online
from playlist import (
    create_playlist,
    download_playlist,
    delete_playlist,
    play_playlist,
    add_inplaylist,
    remove_fromplaylist,
)


def main():
    """
    calls play_song and plays the song
    """
    console = Console()

    while check_connection() is True:

        while True:
            clear_src = "cls" if system().lower().startswith("win") else "clear"
            subprocess.call(clear_src, shell=True)

            song = (
                console.input(
                    Text(
                        "Enter song name | 'O' For more Options\n",
                        style="b #A555EC",
                    )
                )
                .strip()
                .capitalize()
            )

            subprocess.call(clear_src, shell=True)

            options = [
                "Shuffle Play",
                "Play Offline",
                "Download Song",
                "Play Playlist",
                "Create Playlist",
                "Delete Playlist",
                "Download Playlist",
                "Add song in a Playlist",
                "Remove song from a Playlist",
            ]

            match song:

                case "O":

                    option, _ = pick(options=options, title="Options", indicator=">")

                    match option:

                        case "Shuffle Play":

                            shuffle_play()

                        case "Play Offline":

                            try:
                                play_song_offline()
                            except:
                                console.print("No Downloaded Songs Found!")
                                sleep(1)

                        case "Download Song":

                            download_song_name = (
                                console.input(
                                    Text("Enter song name: ", style="#A2DE96")
                                )
                                .capitalize()
                                .strip()
                            )
                            sys.stdout.write("\033[1A[\033[2K[\033[F")

                            download_song(download_song_name)

                        case "Play Playlist":

                            try:
                                play_playlist()
                            except:
                                console.print("Playlist Not Found!")
                                sleep(1)

                        case "Create Playlist":

                            playlist_name = (
                                console.input(
                                    Text("Enter Playlist name: ", style="#2C74B3")
                                )
                                .strip()
                                .capitalize()
                            )
                            sys.stdout.write("\033[1A[\033[2K[\033[F")
                            song_names = (
                                console.input(
                                    Text(
                                        "Enter Song name to add in playlist: ",
                                        style="#2C74B3",
                                    )
                                )
                                .strip()
                                .split(", ")
                            )
                            sys.stdout.write("\033[1A[\033[2K[\033[F")

                            create_playlist(playlist_name, song_names)

                        case "Delete Playlist":

                            try:
                                delete_playlist()
                            except:
                                console.print("No Playlist Available!")
                                sleep(1)

                        case "Download Playlist":

                            try:
                                playlist_todownload = pick(
                                    options=os.listdir(
                                        os.path.join(
                                            os.path.expanduser("~"),
                                            ".aurras",
                                            "Playlists",
                                        )
                                    ),
                                    multiselect=True,
                                    title="Select Playlist[s] to download",
                                    min_selection_count=1,
                                    indicator=">",
                                )
                                for playlist, _ in playlist_todownload:
                                    download_playlist(playlist)
                            except:
                                console.print("Playlist Not Found!")
                                sleep(1)

                        case "Add song in a Playlist":

                            try:
                                table = Table(
                                    show_header=False, header_style="bold magenta"
                                )

                                playlist, _ = pick(
                                    os.listdir(
                                        os.path.join(
                                            os.path.expanduser("~"),
                                            ".aurras",
                                            "Playlists",
                                        )
                                    ),
                                    title="Your Playlists\n\n",
                                    indicator=">",
                                )

                                with open(
                                    os.path.join(
                                        os.path.expanduser("~"),
                                        ".aurras",
                                        "Playlists",
                                        playlist,
                                    ),
                                    "r",
                                    encoding="UTF-8",
                                ) as songs_inplaylist:
                                    table.add_row(songs_inplaylist.read())
                                console.print(table)

                                song_names = (
                                    console.input(
                                        Text(
                                            "Enter Song name to add in playlist: ",
                                            style="#2C74B3",
                                        )
                                    )
                                    .strip()
                                    .split(", ")
                                )
                                sys.stdout.write("\033[1A[\033[2K\033[F")
                                add_inplaylist(playlist, song_names)
                            except:
                                console.print("Playlist Not Found!")
                                sleep(1)

                        case "Remove song from a Playlist":

                            try:
                                playlist, _ = pick(
                                    os.listdir(
                                        os.path.join(
                                            os.path.expanduser("~"),
                                            ".aurras",
                                            "Playlists",
                                        )
                                    ),
                                    title="Your Playlists\n\n",
                                    indicator=">",
                                )
                                remove_fromplaylist(playlist)
                            except:
                                console.print("Playlist Not Found!")
                                sleep(1)

                case _:
                    play_song_online(song)

    console.print("\nNo Internet Connection!\n", style="#FF0000")


def check_connection(host="http://google.com"):
    """
    Checks if connected to network or not
    """
    try:
        with urllib.request.urlopen(host):
            return True
    except:
        return False


def shuffle_play():
    """Plays random songs"""

    playlist_link = [
        "https://music.youtube.com/playlist?list=RDCLAK5uy_ksEjgm3H_7zOJ_RHzRjN1wY-_FFcs7aAU&feature=share&playnext=1",
        "https://music.youtube.com/playlist?list=RDCLAK5uy_n9Fbdw7e6ap-98_A-8JYBmPv64v-Uaq1g&feature=share&playnext=1",
        "https://music.youtube.com/playlist?list=RDCLAK5uy_n9Fbdw7e6ap-98_A-8JYBmPv64v-Uaq1g&feature=share&playnext=1",
        "https://www.youtube.com/playlist?list=PL6k9a6aYB2zk0qSbXR-ZEiwqgdHymsRtQ",
        "https://www.youtube.com/playlist?list=PLO7-VO1D0_6NmK47v6tpOcxurcxdW-hZa",
        "https://www.youtube.com/playlist?list=PL9bw4S5ePsEEqCMJSiYZ-KTtEjzVy0YvK",
    ]

    for _ in range(20):
        top_song = Playlist(random.choice(playlist_link)).video_urls

    while True:
        song = random.choice(top_song)
        play_song_online(song)


if __name__ == "__main__":
    main()
