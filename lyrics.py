"""
Shows lyrics
"""

import keyboard
from rich.table import Table
from rich.console import Console
from googletrans import Translator
from lyrics_extractor import SongLyrics

from term_utils import clear_screen

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

    except Exception:
        pass


def translate_lyrics(song_name: str, song_title: str, close: str):
    """
    Translate lyrics from different language to english
    """

    while not close.is_set():
        table = Table(show_header=False, header_style="bold magenta")

        try:
            temp = SongLyrics.get_lyrics(api_key, song_name)
            lyrics = temp["lyrics"]

            translator = Translator(service_urls=["translate.google.com"])

            translated_lyrics = translator.translate(lyrics, dest="en").text

            keyboard.wait("t")

            if keyboard.is_pressed("t"):
                clear_screen()

                console.print(f"Playing🎶: {song_title}\n", end="\r", style="u #E8F3D6")

                table.add_row(translated_lyrics)
                print("\n\n")
                console.print(table, style="#E5B8F4")

                table = Table(show_header=False, header_style="bold magenta")

        except Exception:
            pass
