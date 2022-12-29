import sys
from time import sleep

for i in range(4):
    print("creating"+ "."*(i))
    sleep(0.8)
    sys.stdout.write("\x1b[1A")
    sys.stdout.write("\x1b[2K")
