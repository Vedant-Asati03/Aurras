"""
Gets songs for shuffle play
"""
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth


def get_songs():
    """
    get songs from trending playlists
    """
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id="451482f891544afba225e80790764cd4",
            client_secret="93bd035368a746a583f4512cffa8cdee",
            redirect_uri="https://developer.spotify.com/dashboard/applaylistications/451482f891544afba225e80790764cd4/users?code=AQBCj_5ixgKlnGJUJgZx0KpSEcfT_n8iaYmZTyRE1kprjOHCnGZXzYgofs1ieBRXHdVVvn5ykG9rqlzaP4wovmk0Rg1i77B_ssQiC6OeH-xeu8Fo_FuOy2UAphKeNiuaqn7MtIdIzfia6TTzvZLzl7pEx-V2TplaylistIQVcrJxOPwISP2qI1AdPfvk0JIofpfp8dJeKCtBWgl_wymAFyb2joAo0PdUge6W7l07xoptZCkpxN2yU35fQ5IhA6rSABzjo",
        )
    )

    try:
        os.mkdir("TrendingSongs")
    except FileExistsError:
        pass


    def get_playlist_feats(playlist_id):
        source_playlistid = playlist_id
        source_playlist = sp.user_playlist("LavaKing", source_playlistid)
        tracks = source_playlist["tracks"]
        songs = tracks["items"]

        track_names = []

        for i in range(0, len(songs)):
            if songs[i]["track"]["id"] is not None:
                track_names.append(songs[i]["track"]["name"])

        return track_names

    # top_2022 = get_playlist_feats("6FIwO0_5Qp2zeVpCuqbbvQ")
    top_2019 = get_playlist_feats("37i9dQZF1Etk7fJUDjOQfi")
    top_2018 = get_playlist_feats("37i9dQZF1Ejqu2YzDW3QW7")
    top_2017 = get_playlist_feats("37i9dQZF1E9WZdF5cHDFWQ")

    files_user = [top_2019, top_2018, top_2017]

    with open(
        os.path.join("TrendingSongs", "trending_songs.txt"), "a", encoding="UTF-8"
    ) as saved_songs:
        for i in range(len(files_user)):
            saved_songs.writelines(f"{files_user[i]}")

get_songs()
