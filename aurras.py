"""
music player
"""
import os
import sys
import shutil
import random
import subprocess
import urllib.request
from time import sleep
from pygame import mixer
from pytube import Playlist
import vlc
import pafy
import pyfiglet
import keyboard
import scrapetube

# import lyricsgenius
from pick import pick
from rich.text import Text
from rich.align import Align
from rich.console import Console
from spotdl import __main__ as spotdl
from youtubesearchpython import Suggestions, VideoSortOrder


def main():
    """
    calls play_song and plays the song
    """

    figlet_text = pyfiglet.figlet_format("AURRAS", font="slant")
    styled_text = Text(figlet_text, style="bold #5f00d7")
    aligned_text = Align(styled_text, align="center")
    console.print(aligned_text)

    while check_connection():

        song = (
            console.input(
                Text(
                    "\nEnter song name | 'D' for downloading song | 'P' for Playing downloaded songs | 'S' for Shuffle play\n>>> ",
                    style="u #6D67E4",
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

            case "S":
                shuffle_play()

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
    # genius = lyricsgenius.Genius(
    #     "Hr8gNt1yrpalcnzSiydi0RuKALquFYKCQXR-EoDnHWo8CuWvbODJJuomiEzq8ogB"
    # )
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
        if keyboard.is_pressed("p"):
            player.set_pause(1)
        # elif keyboard.is_pressed("l"):
        #     print(genius.search_song(song_name).lyrics)


def shuffle_play():
    """
    Plays random songs
    """
    playlist_link = [
        "https://music.youtube.com/playlist?list=RDCLAK5uy_ksEjgm3H_7zOJ_RHzRjN1wY-_FFcs7aAU&feature=share&playnext=1",
        "https://music.youtube.com/playlist?list=RDCLAK5uy_n9Fbdw7e6ap-98_A-8JYBmPv64v-Uaq1g&feature=share&playnext=1",
    ]
    top_songs = Playlist(random.choice(playlist_link)).video_urls

    for _ in range(len(top_songs)):
        while keyboard.is_pressed("p") is False:
            play_song(random.choice(top_songs))
            if keyboard.is_pressed("p") is True:
                break


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


def download_song(song_id: str):
    """
    Downloads song with video
    """
    try:
        os.mkdir("Songs")
    except FileExistsError:
        pass

    subprocess.check_call([sys.executable, spotdl.__file__, song_id])

    for file in os.listdir():
        if file.endswith(".mp3"):
            shutil.move(file, os.path.join("Songs"))


def play_downloaded_songs():
    """
    plays downloaded songs
    """
    mixer.init()

    songs = []
    for song in os.listdir("Songs"):
        songs.append(song)

    selected_song, _ = pick(songs)
    console.print(
        f"\nPlaying: {selected_song.removesuffix('.mp3')}", style="u b #F4EAD5"
    )

    sound = mixer.Sound(os.path.join("Songs", selected_song))
    mixer.Channel(5).play(sound)

    while mixer.Channel(5).get_busy():
        if keyboard.is_pressed("p"):
            mixer.Channel(5).pause()

        elif keyboard.is_pressed("r"):
            mixer.Channel(5).unpause()


if __name__ == "__main__":
    console = Console()
    main()
