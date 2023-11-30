import keyboard
from rich.table import Table
from rich.console import Console
from googletrans import Translator
from lyrics_extractor import SongLyrics

from lib.term_utils import clear_screen


class Lyrics:
    def __init__(self):
        """
        Initialize the LyricsViewer class.
        This class is used to show and translate song lyrics.
        """
        self.api_key = SongLyrics(
            "AIzaSyAcZ6KgA7pCIa_uf8-bYdWR85vx6-dWqDg", "aa2313d6c88d1bf22"
        )
        self.console = Console()


class ShowLyrics(Lyrics):
    def __init__(self, song_user_searched: str):
        super().__init__()
        self.song_user_searched = song_user_searched
        self.lyrics = None
        self._get_lyircs()

    def _get_lyircs(self):
        """"""
        try:
            temp = SongLyrics.get_lyrics(self.api_key, self.song_user_searched)
            self.lyrics = temp["lyrics"]
        except FileNotFoundError:
            pass

    def show_lyrics(self):
        """
        Show lyrics of the song.
        """
        table = Table(show_header=False, header_style="bold magenta")

        table.add_row(self.lyrics)
        print("\n\n")
        self.console.print(table, style="#E5B8F4")
        table = Table(show_header=False, header_style="bold magenta")


# TODO
class TranslateLyrics(Lyrics):
    """..."""

    def __init__(self, song_user_searched: str, song_name_searched: str, close: str):
        """"""
        super().__init__()
        self.song_user_searched = song_user_searched
        self.song_name_searched = song_name_searched
        self.close = close
        self.translator = Translator(
            service_urls=["translate.google.com", "translate.google.co.kr"]
        )
        self.get_lyrics = ShowLyrics(self.song_user_searched)

    def translate_lyrics(self):
        """"""
        while not self.close.is_set():
            table = Table(show_header=False, header_style="bold magenta")
            translated_lyrics = self.translator.translate(
                self.get_lyrics.lyrics, dest="en"
            ).text

            keyboard.wait("t")

            if keyboard.is_pressed("t"):
                clear_screen()

                self.console.print(
                    f"Playing🎶: {self.song_name_searched}\n",
                    end="\r",
                    style="u #E8F3D6",
                )

                table.add_row(translated_lyrics)
                print("\n\n")
                self.console.print(table, style="#E5B8F4")

                table = Table(show_header=False, header_style="bold magenta")
