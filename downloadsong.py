"""
Downloads Songs
"""


import os
import shutil
import subprocess
import sys
from platform import system

from spotdl import __main__ as spotdl


def download_song(song_names: str):
    """
    Downloads song without video
    """
    clr_src = "cls" if system().lower().startswith("win") else "clear"

    try:
        os.makedirs(os.path.join(os.path.expanduser("~"), ".aurras", "Songs"))
    except FileExistsError:
        pass

    for song_name in song_names.split(", "):

        subprocess.check_call([sys.executable, spotdl.__file__, song_name])
        subprocess.call(clr_src, shell=True)

    for file in os.listdir():
        if file.endswith(".mp3"):
            shutil.move(file, os.path.join(os.path.expanduser("~"), ".aurras", "Songs"))
