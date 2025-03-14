#!/usr/bin/env python3
"""
A simplified script for playing multiple songs.

Usage:
  python play_songs.py "song1, song2, song3"
"""

import sys
from aurras.player.online import ListenSongOnline


def main():
    """Play the songs provided as arguments."""
    if len(sys.argv) < 2:
        print("Please provide song names separated by commas.")
        print('Usage: python play_songs.py "song1, song2, song3"')
        return 1

    song_arg = sys.argv[1]
    print(f"Song argument: '{song_arg}'")

    if "," in song_arg:
        songs = [s.strip() for s in song_arg.split(",")]
        print(f"Playing {len(songs)} songs in sequence:")
        for i, song in enumerate(songs, 1):
            print(f"\n[{i}/{len(songs)}] Now playing: {song}")
            player = ListenSongOnline(song)
            player.listen_song_online()
    else:
        print(f"Playing single song: {song_arg}")
        player = ListenSongOnline(song_arg)
        player.listen_song_online()

    return 0


if __name__ == "__main__":
    sys.exit(main())
