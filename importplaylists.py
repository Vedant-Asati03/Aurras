"""
Imports Playlists from other sources
"""

import json
import os
import subprocess

from time import sleep
from platform import system

import spotipy

from pick import pick
from spotipy import util
from rich.console import Console
from rich.text import Text

from playlist import download_playlist


console = Console()


def import_playlist():
    """
    Imports playlist from other platforms
    """

    proceed, _ = pick(
        options=["YES", "NO"],
        title="First you have to Authenticate yourself with [Spotify] | [Youtube]\n\nDo you want to proceed",
        indicator="»",
    )
    clear_src = "cls" if system().lower().startswith("win") else "clear"
    subprocess.call(clear_src, shell=True)

    match proceed:

        case "YES":

            importfrom, _ = pick(
                options=["Spotify", "Youtube"],
                title="Select Platform to import playlist from",
                indicator="»",
            )

            match importfrom:

                case "Spotify":

                    try:
                        if "spotify_auth.json" not in os.listdir(
                            os.path.join(os.path.expanduser("~"), ".aurras")
                        ):

                            client_id = input("Paste Spotify client_id: ")
                            client_secret = input("Paste Spotify client_secret: ")
                            redirect_uri = input("Paste redirect_uri: ")
                            username = input("Write your Spotify username: ")

                            spotify_auth = {
                                "client_id": client_id,
                                "client_secret": client_secret,
                                "redirect_uri": redirect_uri,
                                "username": username,
                                "scope": "playlist-read-private",
                            }

                            with open(
                                os.path.join(
                                    os.path.expanduser("~"),
                                    ".aurras",
                                    "spotify_auth.json",
                                ),
                                "w",
                                encoding="UTF-8",
                            ) as credential_data:

                                json.dump(spotify_auth, credential_data, indent=4)

                    except:
                        pass

                    with open(
                        os.path.join(
                            os.path.expanduser("~"), ".aurras", "spotify_auth.json"
                        ),
                        "r",
                        encoding="UTF-8",
                    ) as credential_data:
                        credentials = json.load(credential_data)

                    token = util.prompt_for_user_token(
                        client_id=credentials["client_id"],
                        client_secret=credentials["client_secret"],
                        scope=credentials["scope"],
                        username=credentials["username"],
                        redirect_uri=credentials["redirect_uri"],
                    )

                    sp = spotipy.Spotify(auth=token)

                    playlists = sp.current_user_playlists()

                    name_id = {}
                    playlists_name = []

                    for user_playlist in playlists["items"]:

                        playlist_name, playlist_id = (
                            user_playlist["name"],
                            user_playlist["id"],
                        )

                        name_id[playlist_name] = playlist_id

                        playlists_name.append(playlist_name)

                    playlist_name, _ = pick(options=playlists_name)

                    tracks = sp.playlist_items(name_id[playlist_name])

                    for track in tracks["items"]:
                        # track["track"]["name"]

                        try:
                            os.makedirs(
                                os.path.join(
                                    os.path.expanduser("~"),
                                    ".aurras",
                                    "Playlists",
                                )
                            )

                        except FileExistsError:
                            pass

                        with open(
                            os.path.join(
                                os.path.expanduser("~"),
                                ".aurras",
                                "Playlists",
                                playlist_name + ".txt",
                            ),
                            "a",
                            encoding="UTF-8",
                        ) as playlist_songs:
                            playlist_songs.write(track["track"]["name"] + "\n")
                    console.print(
                        f"Created Playlist named - {playlist_name}", style="#D09CFA"
                    )
                    ask_user = (
                        console.input(
                            Text(
                                "Do you want to download this playlist [Y]\n",
                                style="#D09CFA",
                            )
                        )
                        .strip()
                        .capitalize()
                    )
                    subprocess.call(clear_src, shell=True)
                    match ask_user:

                        case "Y":
                            download_playlist(playlist_name + ".txt")
                        case _:
                            pass

                    sleep(1.55)

        case "NO":
            pass

        case _:
            pass
