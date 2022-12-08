"""
music player
"""
from time import sleep
import scrapetube
import pafy
import vlc
from rich.console import Console
from rich.align import Align
from rich.text import Text
import pyfiglet


def music_player(song_name):
    """
    plays music
    """
    try:

        video = pafy.new(song_name)
        best = video.getbest()
        playurl = best.url

        instance = vlc.Instance()
        player = instance.media_player_new()
        media = instance.media_new(playurl)
        media.get_mrl()
        player.set_media(media)
        player.play()
        sleep(3)
        while player.is_playing():
            sleep(1)
            command = console.input(Text(">>> ", style="#FFBF00"))
            match command:

                case "p":
                    player.set_pause(1)

    except:
        print("No Internet connection!")


if __name__ == "__main__":
    console = Console()

    figlet_text = pyfiglet.figlet_format("AURRAS", font="slant")
    styled_text = Text(figlet_text, style="bold #5f00d7")
    aligned_text = Align(styled_text, align="center")
    console.print(aligned_text)

    get_song_url = iter(
        scrapetube.get_search(
            console.input(Text("Enter song name: ", style="u #6D67E4")), limit=1
        )
    )
    song = next(get_song_url)["videoId"]

    music_player(song)
