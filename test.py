# import multiprocessing
# import time

# def my_function():
#     print("Running in a new window!")


# if __name__ == '__main__':
#     multiprocessing.freeze_support()
#     p = multiprocessing.Process(target=my_function)
#     p.start()

# import os

# with open(
#     os.path.join(os.path.expanduser("~"), ".aurras", "history.txt"),
#     "a+",
#     encoding="UTF-8",
# ) as history:
#     if os.path.exists((os.path.expanduser("~"), ".aurras", "history.txt")):
#         for item in history.read():
#             print(item)
#     else:
#         print("g")


from __future__ import unicode_literals
import youtube_dl

ydl_opts = {}
with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download(['https://www.youtube.com/@GothamChess'])
