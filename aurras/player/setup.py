"""
MPV Setup Module

This module provides a function for setting up the configuration files for the MPV player.

Example:
    ```
    mpv_setup()
    ```
"""

# Replace absolute import with relative import
from ..utils.path_manager import PathManager

_path_manager = PathManager()


def mpv_setup():
    """
    Create mpv.conf and input.conf files with default configurations.

    This method creates the mpv.conf file with default options and the input.conf file for key bindings.
    """
    _path_manager.mpv_dir.mkdir(parents=True, exist_ok=True)

    # Create the mpv.conf file
    mpv_conf_path = _path_manager.mpv_dir / "mpv.conf"

    if not mpv_conf_path.exists():
        with mpv_conf_path.open("w", encoding="UTF-8") as mpv_conf_file:
            mpv_conf_file.write("--really-quiet\n--no-video\nvolume-max=100\n")

    # Create the input.conf file
    mpv_input_path = _path_manager.mpv_dir / "input.conf"

    if not mpv_input_path.exists():
        with mpv_input_path.open("w", encoding="UTF-8") as mpv_input_file:
            mpv_input_file.write(
                "UP    add volume 7\n"
                "DOWN    add volume -7\n"
                "WHEEL_UP   add volume 2\n"
                "WHEEL_DOWN    add volume -2\n"
                "q    quit\n"
                "b    quit 10\n"  # Exit code 10 for 'previous song'
                "n    quit 11\n"  # Exit code 11 for 'next song'
                "LEFT seek -5\n"
                "RIGHT seek 5\n"
            )
