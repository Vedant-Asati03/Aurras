# import os
# import threading
# import subprocess
# import keyboard


# conf_file = os.path.join(os.path.expanduser("~"), ".aurras", "mpv", "mpv.conf")
# input_file = os.path.join(os.path.expanduser("~"), ".aurras", "mpv", "input.conf")


# def input_thread():
#     # Read input from the user
#     while True:
#         keyboard.wait("l")
#         if keyboard.is_pressed("l"):
#             print(True)


# # Start the input thread
# input_thread = threading.Thread(target=input_thread)
# input_thread.start()

# subprocess.run(
#         f"mpv --include={conf_file} --input-conf={input_file} https://www.youtube.com/watch?v=e4fwY9ZsxPw",
#         shell=True,
#     )

# from googletrans import Translator

# translator = Translator()

# print(translator.translate("जग", dest="en").text)


# import os

# # Run the `where` command to find the location of the libmpv.dll library
# result = os.popen("where libmpv.dll").read()

# # Print the path to the library
# print(result)


# import mpv

# player = mpv.MPV()

# if player._playback_cond == "playing":
#     print(True)
