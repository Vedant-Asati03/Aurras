"""
MPV Setup Module

This module provides a function for setting up the configuration files for the MPV player.

Example:
    ```
    mpv_setup()
    ```
"""

import os
import config as path


def mpv_setup():
    """
    Create mpv.conf and input.conf files with default configurations.

    This method creates the mpv.conf file with default options and the input.conf file for key bindings.
    """
    try:
        os.makedirs(path.mpv)

        # Create the mpv.conf file
        with open(
            os.path.join(path.mpv, "mpv.conf"), "w", encoding="UTF-8"
        ) as mpv_conf_file:
            mpv_conf_file.write("--really-quiet\n--no-video\nvolume-max=130\n")

        # Create the input.conf file
        with open(
            os.path.join(path.mpv, "input.conf"), "w", encoding="UTF-8"
        ) as mpv_input_file:
            mpv_input_file.write(
                "UP    add volume 7\nDOWN    add volume -7\nWHEEL_UP   add volume 2\nWHEEL_DOWN    add volume -2\nq    quit\n"
            )

    except FileExistsError:
        pass
