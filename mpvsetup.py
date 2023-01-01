"""
Creates
mpv.conf file - For default configurations like no-video, 
and
input.conf file
"""

import os
import sys


def mpv_setup():
    """
    Setting up mpv
    """

    try:
        os.makedirs(os.path.join(os.path.expanduser("~"), "AURRAS", "mpv"))

    except FileExistsError:
        sys.exit()

    path = os.path.join(os.path.expanduser("~"), "AURRAS", "mpv")

    # Creates a mpv.conf file
    with open(os.path.join(path, "mpv.conf"), "w", encoding="UTF-8") as mpv_conf_file:

        mpv_conf_file.write("--really-quiet\n--no-video\nvolume-max=130\n")

    # Creates a input.conf file
    with open(
        os.path.join(path, "input.conf"), "w", encoding="UTF-8"
    ) as mpv_input_file:

        mpv_input_file.write(
            "UP    add volume 7\nDOWN    add volume -7\nWHEEL_UP   add volume 2\nWHEEL_DOWN    add volume -2\nc    quit\n"
        )
