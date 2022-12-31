import mpv

# Create an instance of the MPV player
player = mpv.MPV()

# Set the path to the MP3 file you want to play
player.play("D:\\PYTHON PROJECTS\\Aurras\\Songs\\Ed Sheeran - Perfect.mp3")

# Wait for the song to finish playing
player.wait_for_playback()
