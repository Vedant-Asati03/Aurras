from pprint import pprint
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials  # To access authorised Spotify data
from ytmusicapi import YTMusic


yt = YTMusic("auth.json")

# search_results = yt.search("kesariya")
# pprint(search_results)

CLIENTID = "451482f891544afba225e80790764cd4"
CLIENTSECRET = "93bd035368a746a583f4512cffa8cdee"
client_credentials_manager = SpotifyClientCredentials(
    client_id=CLIENTID, client_secret=CLIENTSECRET
)

sp = spotipy.Spotify(
    client_credentials_manager=client_credentials_manager
)  # spotify object to access API

# NAME = "AJR"  # chosen artist
# for res in search_results:
#     for name in (res["artists"]):
#         chan_id = name["id"]
#     break

# genre = []
# artist = yt.get_artist(channelId=chan_id)
# # pprint(artist)
# for i in artist["related"]["results"]:
#     NAME = i["title"]
    # result = sp.search(NAME)  # search query
    # genre.append(result["tracks"]["items"][0]["artists"])

# print(result)
# print(result["tracks"]["items"][0]["artists"])
# print(genre)

# print(sp.new_releases())
# for res in sp.new_releases()["albums"]["items"]:
#     print(res["name"])

# print(sp.search("kesariya"))
artists = []
for i in sp.search("kesariya")["tracks"]["items"]:
    URI = i["album"]["uri"]
    artists.append(sp.artist_related_artists(URI))
pprint(artists)
