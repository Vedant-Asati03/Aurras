"""
MPV Setup Module

This module provides a function for setting up the configuration files for the MPV player.

Example:
    ```
    mpv_setup()
    ```
"""

from config import path


def mpv_setup():
    """
    Create mpv.conf and input.conf files with default configurations.

    This method creates the mpv.conf file with default options and the input.conf file for key bindings.
    """
    path.mpv.mkdir(parents=True, exist_ok=True)

    # Create the mpv.conf file
    mpv_conf_path = path.mpv / "mpv.conf"

    if not mpv_conf_path.exists():
        with mpv_conf_path.open("w", encoding="UTF-8") as mpv_conf_file:
            mpv_conf_file.write("--really-quiet\n--no-video\nvolume-max=100\n")

    # Create the input.conf file
    mpv_input_path = path.mpv / "input.conf"

    if not mpv_input_path.exists():
        with mpv_input_path.open("w", encoding="UTF-8") as mpv_input_file:
            mpv_input_file.write(
                "UP    add volume 7\nDOWN    add volume -7\nWHEEL_UP   add volume 2\nWHEEL_DOWN    add volume -2\nq    quit\n"
            )
