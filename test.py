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



from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory

# Create a FileHistory object
history = FileHistory('command_history.txt')

# Prompt the user for input with command history enabled
user_input = prompt('Enter your command: ', history=history)

# Print the entered command
print(f'Command entered: {user_input}')

# Access previous commands in the history
for past_command in history.read():
    print(f'Past command: {past_command}')
