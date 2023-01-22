"""
Shows lyrics
"""

import subprocess
import threading
from platform import system

import keyboard
from googletrans import Translator
from lyrics_extractor import SongLyrics
from rich.console import Console
from rich.table import Table

CLRSRC = "cls" if system().lower().startswith("win") else "clear"

api_key = SongLyrics("AIzaSyAcZ6KgA7pCIa_uf8-bYdWR85vx6-dWqDg", "aa2313d6c88d1bf22")

console = Console()


def show_lyrics(song_name: str):
    """
    Prints lyrics of the song
    """
    table = Table(show_header=False, header_style="bold magenta")

    try:

        temp = SongLyrics.get_lyrics(api_key, song_name)
        lyrics = temp["lyrics"]

        table.add_row(lyrics)
        print("\n\n")
        console.print(table, style="#E5B8F4")
        table = Table(show_header=False, header_style="bold magenta")

        lyrics_tranlation = threading.Thread(
            target=translate_lyrics,
            daemon=True,
            args=(
                song_name,
                lyrics,
            ),
        )
        lyrics_tranlation.start()

    except:
        pass


def translate_lyrics(song_name: str, lyrics: str):
    """
    Translate lyrics of different language in english
    """

    table = Table(show_header=False, header_style="bold magenta")

    while True:

        keyboard.wait("t")

        if keyboard.is_pressed("t"):

            subprocess.call(CLRSRC, shell=True)

            translator = Translator(service_urls=["translate.google.com"])

            translated_lyrics = translator.translate(lyrics, dest="en").text

            console.print(f"Playing🎶: {song_name}\n", end="\r", style="u #E8F3D6")

            table.add_row(translated_lyrics)
            print("\n\n")
            console.print(table, style="#E5B8F4")

            table = Table(show_header=False, header_style="bold magenta")
