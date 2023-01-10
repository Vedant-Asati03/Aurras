import os
import subprocess
import select


conf_file = os.path.join(os.path.expanduser("~"), ".aurras", "mpv", "mpv.conf")
input_file = os.path.join(os.path.expanduser("~"), ".aurras", "mpv", "input.conf")


# Start playing an audio file using mpv and subprocess.run
mpv_process = subprocess.Popen(
    [
        "mpv",
        f"--include={conf_file}",
        f"--input-conf={input_file}",
        "C:\\Users\\vedan\\.aurras\\Downloaded-Playlists\\♥️You3000\\Avicii - The Nights.mp3",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True,
)


# Display a progress bar while the audio file is playing
while True:
    # Use the select module to check if the mpv process has any output available to be read
    ready_to_read, _, _ = select.select([mpv_process.stdout], [], [], 0.1)

    # If the mpv process has output available to be read, retrieve the current position and duration of the audio file
    if ready_to_read:
        position = mpv_process.stdout.readline().strip()
        duration, _ = mpv_process.communicate("get_property duration\n")

        # If the position or duration is not available, break out of the loop
        if position is None or duration is None:
            break

        # Calculate the percentage of the audio file that has been played
        progress = (float(position) / float(duration)) * 100

        # Display the progress bar in the terminal
        print(f"\r[{'#' * int(progress):50}] {int(progress)}%", end="")

# Clear the progress bar when the audio file has finished playing
print("\r", end="")
