"""
Shows lyrics
"""

# import subprocess

from platform import system

# import keyboard

from rich.table import Table
from rich.console import Console
# from googletrans import Translator
from lyrics_extractor import SongLyrics


console = Console()

table = Table(show_header=False, header_style="bold magenta")

CLRSRC = "cls" if system().lower().startswith("win") else "clear"

api_key = SongLyrics("AIzaSyAcZ6KgA7pCIa_uf8-bYdWR85vx6-dWqDg", "aa2313d6c88d1bf22")


def show_lyrics(song_name: str):
    """
    Prints lyrics of the song
    """

    try:
        temp = SongLyrics.get_lyrics(api_key, song_name)
        lyrics = temp["lyrics"]

        table.add_row(lyrics)
        print("\n\n")
        console.print(table, style="#E5B8F4")
    except:
        pass


# def translate_lyrics(song_name: str, song_title: str):
#     """
#     Translate lyrics of different language in english
#     """

#     while True:

#         keyboard.wait("t")

#         if keyboard.is_pressed("t"):

#             subprocess.call(CLRSRC, shell=True)

#             translator = Translator()

#             try:
#                 temp = SongLyrics.get_lyrics(api_key, song_name)
#                 lyrics = temp["lyrics"]

#             except:
#                 pass

#             translated_lyrics = translator.translate(lyrics, dest="en").text

#             console.print(f"Playing🎶: {song_title}\n", end="\r", style="u #E8F3D6")

#             table.add_row(translated_lyrics)
#             print("\n\n")
#             console.print(table, style="#E5B8F4")
