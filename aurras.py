"""
Music-Player
"""

import os
import random
import threading
from time import sleep

from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from pick import pick
from rich.text import Text
from rich.table import Table
from rich.console import Console
from logger import exception_log

from recommendation import recommend_songs
from downloadsong import download_song
from term_utils import clear_screen
from playlist import (
    add_inplaylist,
    create_playlist,
    delete_playlist,
    download_playlist,
    import_playlist,
    play_playlist,
    remove_fromplaylist,
)
from playsong import (
    play_song_offline,
    play_song_online,
    shuffle_play,
)


def main():
    """
    calls play_song and plays the song
    """
    console = Console()

    while True:
        clear_screen()

        recent_songs_file = os.path.join(
            os.path.expanduser("~"), ".aurras", "recently_played_songs.txt"
        )
        recent_songs = FileHistory(recent_songs_file)
        recommendations = [
            "Shuffle Play",
            "Play Offline",
            "Download Song",
            "Play Playlist",
            "Create Playlist",
            "Delete Playlist",
            "Import Playlist",
            "Download Playlist",
            "Add song in a Playlist",
            "Remove song from a Playlist",
        ]

        if os.path.exists(
            os.path.join(os.path.expanduser("~"), ".aurras", "recommended_songs.txt")
        ):
            with open(
                os.path.join(
                    os.path.expanduser("~"), ".aurras", "recommended_songs.txt"
                ),
                "r",
                encoding="UTF-8",
            ) as recommended_list:
                reader = recommended_list.readlines()
                random.shuffle(reader)

                for recommended_song in reader[-10:]:
                    recommendations.append(recommended_song)

        class Recommend(Completer):
            def get_completions(self, document, complete_event):
                """
                auto completes
                """
                completions = [
                    Completion(recommendation, start_position=0)
                    for recommendation in recommendations
                ]
                return completions

        style = Style.from_dict(
            {
                "placeholder": "ansilightgray",
            }
        )

        song = (
            prompt(
                completer=Recommend(),
                placeholder="Search Song",
                style=style,
                complete_while_typing=True,
                clipboard=True,
                mouse_support=True,
                history=recent_songs,
                auto_suggest=AutoSuggestFromHistory(),
            )
            .strip()
            .lower()
        )

        clear_screen()

        match song:
            case "shuffle play":
                stop_playing_event = threading.Event()

                thread_shuffle_play = threading.Thread(
                    target=shuffle_play, args=(stop_playing_event,)
                )
                thread_shuffle_play.start()

                try:
                    while True:
                        pass
                except KeyboardInterrupt:
                    stop_playing_event.set()

                thread_shuffle_play.join()

                clear_screen()

            case "play offline":
                try:
                    play_song_offline()
                except Exception as e:
                    exception_log(e)
                    console.print("No Downloaded Songs Found!")
                    sleep(1)

            case "download song":
                download_song_name = (
                    console.input(Text("Enter song name: ", style="#A2DE96"))
                    .capitalize()
                    .strip()
                )
                print("\033[1A[\033[2K[\033[F")

                download_song(download_song_name)

            case "play playlist":
                try:
                    play_playlist()
                except Exception:
                    console.print("Playlist Not Found!")
                    sleep(1)

            case "create playlist":
                playlist_name = (
                    console.input(Text("Enter Playlist name: ", style="#2C74B3"))
                    .strip()
                    .capitalize()
                )
                print("\033[1A[\033[2K[\033[F")

                song_names = prompt(
                    console.input(
                        Text(
                            "Enter Song name to add in playlist: ",
                            style="#2C74B3",
                        )
                    )
                    .strip()
                    .split(", ")
                )

                print("\033[1A[\033[2K[\033[F")

                create_playlist(playlist_name, song_names)

            case "delete playlist":
                try:
                    delete_playlist()
                except Exception:
                    console.print("No Playlist Available!")
                    sleep(1)

            case "import playlist":
                import_playlist()

            case "download playlist":
                try:
                    playlist_to_download = pick(
                        options=os.listdir(
                            os.path.join(
                                os.path.expanduser("~"),
                                ".aurras",
                                "Playlists",
                            )
                        ),
                        multiselect=True,
                        title="Select Playlist[s] to download",
                        min_selection_count=1,
                        indicator=">",
                    )
                    for playlist, _ in playlist_to_download:
                        download_playlist(playlist)
                except Exception:
                    console.print("Playlist Not Found!")
                    sleep(1)

            case "add song in a playlist":
                try:
                    table = Table(show_header=False, header_style="bold magenta")

                    playlist, _ = pick(
                        os.listdir(
                            os.path.join(
                                os.path.expanduser("~"),
                                ".aurras",
                                "Playlists",
                            )
                        ),
                        title="Your Playlists\n\n",
                        indicator="»",
                    )

                    with open(
                        os.path.join(
                            os.path.expanduser("~"),
                            ".aurras",
                            "Playlists",
                            playlist,
                        ),
                        "r",
                        encoding="UTF-8",
                    ) as songs_inplaylist:
                        table.add_row(songs_inplaylist.read())
                    console.print(table)

                    song_names = (
                        console.input(
                            Text(
                                "Enter Song name to add in playlist: ",
                                style="#2C74B3",
                            )
                        )
                        .strip()
                        .split(", ")
                    )
                    print("\033[1A[\033[2K\033[F")
                    add_inplaylist(playlist, song_names)
                except Exception:
                    console.print("Playlist Not Found!")
                    sleep(1)

            case "remove song from a playlist":
                try:
                    playlist, _ = pick(
                        os.listdir(
                            os.path.join(
                                os.path.expanduser("~"),
                                ".aurras",
                                "Playlists",
                            )
                        ),
                        title="Your Playlists\n\n",
                        indicator=">",
                    )
                    remove_fromplaylist(playlist)
                except Exception:
                    console.print("Playlist Not Found!")
                    sleep(1)

            case _:
                recommend_songs(song)
                play_song_online(song)


if __name__ == "__main__":
    c = Console()
    try:
        main()

    except KeyboardInterrupt:
        c.print("[bold green]Thanks for using aurras![/]")

    except Exception:
        c.print("[bold red]Oh no! An unknown error occured.[/]")
        c.print(
            "[bold red] Please report it on https://github.com/Vedant-Asati03/aurras/issues with the following exception traceback: [/]"
        )
        c.print_exception()
