"""
music player
"""

try:
    import os
    import sys
    import shutil
    import random
    import keyboard
    import subprocess
    import urllib.request

    from time import sleep
    from requests import get
    from pick import pick
    from platform import system
    from pytube import Playlist
    from rich.text import Text
    from rich.console import Console
    from youtube_dl import YoutubeDL
    from spotdl import __main__ as spotdl

    from lyrics import show_lyrics
    from playlist import create_playlist, view_playlist, delete_playlist, add_inplaylist

except Exception:
    pass


def main():
    """
    calls play_song and plays the song
    """

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
                .capitalize()
                .strip()
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
                    delete_playlist(view_playlist())

                case "A":

                    playlist_name = view_playlist()
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
                    add_inplaylist(playlist_name, song_names)

                case "V":
                    path = os.path.join(
                        os.path.expanduser("~"), "AURRAS", "PLAYLISTS", view_playlist()
                    )

                    with open(path, "r", encoding="UTF-8") as current_playlists:
                        print(current_playlists.read())
                        if keyboard.read_key() is True:
                            sys.stdout.write("\033[F")
                            subprocess.call(clear_src, shell=True)

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
    except Exception:
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


def play_song(song_name: str):
    """
    Searches for song
    """
    ydl_opts = {
        "format": "bestaudio",
        "noplaylist": "True",
        "skipdownload": "True",
        "quiet": "True",
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            get(song_name, timeout=20)
        except Exception:
            audio = ydl.extract_info(f"ytsearch:{song_name}", download=False)[
                "entries"
            ][0]
        else:
            audio = ydl.extract_info(song_name, download=False)

    song_title = audio["title"]
    song_url = audio["webpage_url"]

    console.print(f"Playing🎶: {song_title}\n", end="\r", style="u #E8F3D6")
    show_lyrics(song_title)
    os.system("mpv " + song_url)


def download_song(song_id: str):
    """
    Downloads song without video
    """
    try:
        os.mkdir("Songs")
    except FileExistsError:
        pass

    subprocess.check_call([sys.executable, spotdl.__file__, song_id])

    for file in os.listdir():
        if file.endswith(".mp3"):
            shutil.move(file, os.path.join("Songs"))
    sleep(0.5)


def play_downloaded_songs():
    """
    plays downloaded songs
    """

    songs = []
    for song in os.listdir("Songs"):
        songs.append(song)

    selected_song, _ = pick(songs)
    console.print(
        f"\nPlaying: {selected_song.removesuffix('.mp3')}", style="u b #F4EAD5"
    )

    os.system("mpv " + selected_song)


if __name__ == "__main__":
    console = Console()
    main()
