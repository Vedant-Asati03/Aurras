"""
music player
"""
from time import sleep
import scrapetube
import pafy
import vlc


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
        sleep(2)
        while player.is_playing():
            sleep(1)
            command = input(">>> ")
            match command:

                case "p":
                    player.set_pause(1)

                case "r":
                    player.play()

    except:
        print("No Internet connection!")


if __name__ == "__main__":
    get_song_url = iter(scrapetube.get_search(input("Enter song name: "), limit=1))
    song = next(get_song_url)["videoId"]

    music_player(song)
