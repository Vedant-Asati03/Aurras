# import multiprocessing
# import time

# def my_function():
#     print("Running in a new window!")


# if __name__ == '__main__':
#     multiprocessing.freeze_support()
#     p = multiprocessing.Process(target=my_function)
#     p.start()

# import os

# with open(
#     os.path.join(os.path.expanduser("~"), ".aurras", "history.txt"),
#     "a+",
#     encoding="UTF-8",
# ) as history:
#     if os.path.exists((os.path.expanduser("~"), ".aurras", "history.txt")):
#         for item in history.read():
#             print(item)
#     else:
#         print("g")

# import spotipy
# from spotipy.oauth2 import SpotifyClientCredentials

# def recommended_songs(song_name):
#     # Set up Spotify API credentials
#     client_id = '451482f891544afba225e80790764cd4'
#     client_secret = 'fbfc0d6265ca4a5ca3f203abf5c69173'
#     client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
#     sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

#     # Search for the given song
#     results = sp.search(q=song_name, limit=1, type='track')

#     if len(results['tracks']['items']) > 0:
#         song_id = results['tracks']['items'][0]['id']

#         # Get related songs based on the song ID
#         related_songs = sp.recommendations(seed_tracks=[song_id], limit=10)['tracks']

#         # Extract the related song names
#         related_song_names = [song['name'] for song in related_songs]

#         return related_song_names
#     else:
#         return []

# # Example usage
# song_name = 'shape of you'
# related_songs = recommended_songs(song_name)
# print(f"Related songs for '{song_name}':")
# for song in related_songs:
#     print(song)


# from prompt_toolkit import prompt
# from prompt_toolkit.completion import Completer, Completion

# # List of recommendations
# recommendations = ['recommendation1', 'recommendation2', 'recommendation3']

# # Custom completer class
# class MyCompleter(Completer):
#     def get_completions(self, document, complete_event):
#         completions = [
#             Completion(recommendation, start_position=0)
#             for recommendation in recommendations
#         ]
#         return completions

# # Prompt the user for input with the custom completer
# user_input = prompt('Enter your input: ', completer=MyCompleter(), complete_while_typing=True)

# # Print the user input
# print(f'You entered: {user_input}')


# from prompt_toolkit import prompt
# from prompt_toolkit.history import FileHistory
# from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

# # Create a history object with a file path
# history = FileHistory('recently_played_songs.txt')

# # Prompt the user for input with auto-suggestions from history
# user_input = prompt(
#     'Enter a command: ',
#     history=history,
#     auto_suggest=AutoSuggestFromHistory(),
# )

# print(f'You entered: {user_input}')


# from prompt_toolkit import PromptSession
# from prompt_toolkit.history import InMemoryHistory
# from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion

# recommendations = [
#     "Shuffle Play",
#     "Play Offline",
#     "Download Song",
#     "Play Playlist",
#     "Create Playlist",
#     "Delete Playlist",
#     "Import Playlist",
#     "Download Playlist",
#     "Add song in a Playlist",
#     "Remove song from a Playlist",
# ]

# class RecommendAutoSuggest(AutoSuggest):
#     def __init__(self, suggestions):
#         self.suggestions = suggestions

#     def get_suggestion(self, buffer, document):
#         text = document.text_before_cursor.lower()
#         if text:
#             for suggestion in self.suggestions:
#                 if suggestion.lower().startswith(text):
#                     return Suggestion(suggestion)
#         return None

# history = InMemoryHistory()
# auto_suggest = RecommendAutoSuggest(recommendations)

# session = PromptSession(
#     history=history,
#     auto_suggest=auto_suggest,
#     complete_while_typing=True,
#     mouse_support=True,
# )

# song = session.prompt("Search Song\n").strip().lower()

# print(f"You entered: {song}")


# from prompt_toolkit import prompt
# from prompt_toolkit.application import Application
# from prompt_toolkit.key_binding import KeyBindings

# # Define custom key bindings
# kb = KeyBindings()

# @kb.add('a')
# def _(event):
#     print('Key "a" is pressed!')

# # Create an application
# app = Application(key_bindings=kb)

# # Start the application event loop
# app.run()

# import os
# import sqlite3

# path_recommendations = os.path.join(
#     os.path.expanduser("~"), ".aurras", "spotify_auth.db"
# )

# with sqlite3.connect(path_recommendations) as recommendation:
#     cursor = recommendation.cursor()

#     cursor.execute("SELECT client_id, client_secret, scope, username, redirect_uri FROM spotify_auth")

#     row = cursor.fetchone()

#     print(row[0])

# import yt_dlp

# def download_video(url):
#     options = {
#         'format': 'bestaudio/best',
#         'extractaudio': True,  # Download audio only
#         'audioformat': 'mp3',  # Save as MP3
#         'outtmpl': '%(title)s.%(ext)s',  # Output file name template
#     }

#     with yt_dlp.YoutubeDL(options) as ydl:
#         ydl.download([url])

# # Example URL: Replace this with the YouTube video URL you want to download
# video_url = 'https://www.youtube.com/shorts/j40mcWP0PqU'

# download_video(video_url)


# import questionary

# def select_programming_language():
#     choices = ["Python", "JavaScript", "Java", "C++"]
#     return questionary.autocomplete(
#         "Select a programming language:",
#         choices=choices
#     ).ask()

# selected_language = select_programming_language()
# print(f"You selected: {selected_language}")



import os
import sqlite3


with sqlite3.connect(
    os.path.join(os.path.expanduser("~"), ".aurras", "playlists.db")
) as check:
    cursor = check.cursor()
    cursor.execute(f"SELECT * FROM MadeForMe")

    # Fetch all rows
    rows = cursor.fetchall()

    # Process the fetched rows (e.g., print them)
    for row in rows:
        print(row[1])
