"""
music player
"""

import os
import sys
import shutil
import random
import subprocess
import urllib.request

from platform import system

from pick import pick
from pytube import Playlist
from rich.text import Text
from rich.console import Console
from rich.table import Table
from spotdl import __main__ as spotdl

from playsong import play_song
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
                        "Enter song name | 'D' for downloading song | 'P' for Playing downloaded songs | 'S' for Shuffle play\n",
                        style="i #6D67E4",
                    )
                )
                .strip()
                .capitalize()
            )

            subprocess.call(clear_src, shell=True)

            match song:

                case "D":

                    download_song_name = (
                        console.input(Text("Enter song name: ", style="#A2DE96"))
                        .capitalize()
                        .strip()
                    )
                    sys.stdout.write("\033[1A[\033[2K[\033[F")

                    download_song(download_song_name)

                case "P":

                    play_downloaded_songs()

                case "S":

                    shuffle_play()

                case "C":

                    playlist_name = (
                        console.input(Text("Enter Playlist name: ", style="#2C74B3"))
                        .strip()
                        .capitalize()
                    )
                    sys.stdout.write("\033[1A[\033[2K[\033[F")
                    song_names = (
                        console.input(
                            Text(
                                "Enter Song name to add in playlist: ", style="#2C74B3"
                            )
                        )
                        .strip()
                        .split(", ")
                    )
                    sys.stdout.write("\033[1A[\033[2K[\033[F")

                    create_playlist(playlist_name, song_names)

                case "R":

                    delete_playlist()

                case "A":

                    table = Table(show_header=False, header_style="bold magenta")

                    playlist, _ = pick(
                        os.listdir(
                            os.path.join(os.path.expanduser("~"), "AURRAS", "PLAYLISTS")
                        ),
                        title="Your Playlists\n\n",
                        indicator=">",
                    )

                    with open(
                        os.path.join(
                            os.path.expanduser("~"), "AURRAS", "PLAYLISTS", playlist
                        ),
                        "r",
                        encoding="UTF-8",
                    ) as songs_inplaylist:
                        table.add_row(songs_inplaylist.read())
                    console.print(table)

                    song_names = (
                        console.input(
                            Text(
                                "Enter Song name to add in playlist: ", style="#2C74B3"
                            )
                        )
                        .strip()
                        .split(", ")
                    )
                    sys.stdout.write("\033[1A[\033[2K\033[F")
                    add_inplaylist(playlist, song_names)

                case "Y":

                    playlist, _ = pick(
                        os.listdir(
                            os.path.join(os.path.expanduser("~"), "AURRAS", "PLAYLISTS")
                        ),
                        title="Your Playlists\n\n",
                        indicator=">",
                    )
                    remove_fromplaylist(playlist)

                case "V":

                    play_playlist()

                case "X":

                    try:
                        playlist_todownload = pick(
                            options=os.listdir(
                                os.path.join(
                                    os.path.expanduser("~"), "AURRAS", "PLAYLISTS"
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
                        console.print("No Playlist Found!")

                case _:
                    play_song(song)

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
        os.system("mpv " + song)


def download_song(song_name: str):
    """
    Downloads song without video
    """
    clr_src = "cls" if system().lower().startswith("win") else "clear"

    try:
        os.makedirs(os.path.join(os.path.expanduser("~"), "AURRAS", "SONGS"))
    except FileExistsError:
        pass

    subprocess.check_call([sys.executable, spotdl.__file__, song_name])
    subprocess.call(clr_src, shell=True)

    for file in os.listdir():
        if file.endswith(".mp3"):
            shutil.move(file, os.path.join(os.path.expanduser("~"), "AURRAS", "SONGS"))


def play_downloaded_songs():
    """
    plays downloaded songs
    """
    console = Console()

    songs = []
    for song in os.listdir("Songs"):
        songs.append(song)

    selected_song, _ = pick(songs)
    console.print(
        f"\nPlaying: {selected_song.removesuffix('.mp3')}", style="u b #F4EAD5"
    )

    os.system("mpv " + selected_song)


if __name__ == "__main__":
    main()
