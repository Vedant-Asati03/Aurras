"""
Shows lyrics
"""
from lyrics_extractor import SongLyrics
from rich.console import Console
from rich.table import Table


def show_lyrics(song_name: str):
    """
    Prints lyrics of the song
    """
    console = Console()
    table = Table(show_header=False, header_style="bold magenta")

    api_key = SongLyrics("AIzaSyAcZ6KgA7pCIa_uf8-bYdWR85vx6-dWqDg", "aa2313d6c88d1bf22")

    try:
        temp = SongLyrics.get_lyrics(api_key, song_name)
        lyrics = temp["lyrics"]

        # console.print(f"\n\n\n{lyrics}", style="#E5B8F4")
        table.add_row(lyrics)
        print("\n\n")
        console.print(table, style="#E5B8F4")
    except:
        pass
