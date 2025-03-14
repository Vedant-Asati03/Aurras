#!/usr/bin/env python3
"""
Debug script for testing command-line argument handling in Aurras.
"""

import sys
import argparse


def main():
    """Test how command-line arguments are processed."""
    print("Command-line arguments:")
    for i, arg in enumerate(sys.argv):
        print(f"  Arg {i}: '{arg}'")

    # Set up argument parser for command-line arguments
    parser = argparse.ArgumentParser(
        description="Debug command-line arguments",
    )
    parser.add_argument("song", nargs="?", help="Play a song directly")

    # Parse arguments
    args = parser.parse_args()

    print("\nParsed arguments:")
    print(f"  Song: '{args.song}'")

    if args.song and "," in args.song:
        songs = [s.strip() for s in args.song.split(",")]
        print("\nSplit into multiple songs:")
        for i, song in enumerate(songs):
            print(f"  Song {i + 1}: '{song}'")

    print("\nTo test this with commas, use quotes:")
    print('  python debug_cli.py "song1, song2, song3"')


if __name__ == "__main__":
    main()
