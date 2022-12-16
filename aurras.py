"""
music player
"""
import os
import sys
import shutil
import subprocess
import urllib.request
from time import sleep
import vlc
import pafy
import pyfiglet
import scrapetube
from pick import pick
from rich.text import Text
from rich.align import Align
from rich.console import Console
from spotdl import __main__ as spotdl
from youtubesearchpython import Suggestions, VideoSortOrder
from TrendingSongs.get_trending_songs import get_songs


def main():
    """
    calls play_song and plays the song
    """

    figlet_text = pyfiglet.figlet_format("AURRAS", font="slant")
    styled_text = Text(figlet_text, style="bold #5f00d7")
    aligned_text = Align(styled_text, align="center")
    console.print(aligned_text)

    while check_connection():
        if os.path.exists(os.path.join("TrendingSongs", "trending_songs.txt")) is True:
            pass
        else:
            get_songs()

        song = (
            console.input(
                Text(
                    "\nEnter song name | 'D' for downloading song : ", style="u #6D67E4"
                )
            )
            .capitalize()
            .strip()
        )

        match song:

            case "D":

                download_song_name = console.input(
                    Text("Enter song name: ", style="#A2DE96")
                ).capitalize()

                download_song(download_song_name)

            case "P":
                play_downloaded_songs()

            case _:

                print(f"Playing🎶: {song}\n")
                play_song(search_song(song))

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


def play_song(song_id):
    """
    plays music
    """
    audio = pafy.new(song_id).getbestaudio().url

    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(audio)
    media.get_mrl()
    player.set_media(media)
    player.play()
    sleep(5)
    while player.is_playing():
        sleep(1)
        command = console.input(Text(">>> ", style="#FFBF00"))
        match command:

            case "p":
                player.set_pause(1)


def shuffle_play():
    """
    Plays random songs
    """
    """
    https://www.youtube.com/watch?v=kJQP7kiw5Fk&list=PL15B1E77BB5708555
    """


def download_song(songid: str):
    """
    Downloads song with video
    """
    try:
        os.mkdir("Songs")
    except FileExistsError:
        pass

    subprocess.check_call([sys.executable, spotdl.__file__, songid])

    for file in os.listdir("Songs"):
        if file.endswith(".mp3"):
            shutil.move(file, os.path.join("Songs"))


def search_song(song_name):
    """
    searches for videoid from title
    """
    song_results = []

    suggestions = Suggestions(VideoSortOrder.relevance)

    for songs in suggestions.get(song_name)["result"]:
        song_results.append(songs.capitalize())

    selected_song = iter(scrapetube.get_search(pick(song_results)))
    return next(selected_song)["videoId"]


def play_downloaded_songs():
    """
    plays downloaded songs
    """

    songs = []
    for song in os.listdir():
        songs.append(song)

    selected_song, _ = pick(songs)
    print(selected_song)

    vlc.MediaPlayer(os.path.dirname(os.path.abspath(selected_song))).play()


if __name__ == "__main__":
    console = Console()
    main()
