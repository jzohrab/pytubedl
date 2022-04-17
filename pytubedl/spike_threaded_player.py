# open the full file
# audio of first 10 seconds
# vosk it

from pydub import AudioSegment
from pydub import playback
from pydub.silence import split_on_silence
import os
import sys

from console.utils import wait_key

######################
# Player

import threading
from multiprocessing import Process, Queue
import time

class Player:

    def __init__(self, chunks):
        self.chunks = chunks
        self.maxindex = len(self.chunks)
        self.index = 0
        self.proc = None

    def next_thing(self):
        print("called next_thing", end = "\r\n")
        pass

    def play_chunk(self):
        print(f"  playing {self.index}", end = "\r\n")
        time.sleep(10)
        print("  done playing", end = "\r\n")
        self.index += 1
        if (self.index < self.maxindex):
            self.play()

    def play(self):
        # Start current chunk on a thread.
        # Calls back when it's done.
        # ??
        print(f"called play with index = {self.index}", end = "\r\n")
        p = Process(target=self.play_chunk)
        p.daemon = True
        self.proc = p
        self.proc.start()
        print(f"end of call to play with index {self.index}", end = "\r\n")

    def gotcommand(self, t):
        print("got command : " + t, end = "\r\n")
        if (t == 'q'):
            self.proc.terminate()

######################
# Main

f = "downloads/test_split.mp3"
print("loading song")
song = AudioSegment.from_mp3(f)
print("first x seconds")
duration = 10 * 1000  # ms
song = song[:duration]
print("split")

# Splitting takes a while ... perhaps background this somehow.
print('splitting on silence ...')
# Split track
chunks = split_on_silence (
    song, 
    # check every X ms for silence check ... no need to check every single millisecond
    seek_step = 50,
    # Without keep_silence = True, the clips get cut off prematurely.
    # There appears to be something wrong with the split_on_silence
    # algorithm (some boundary error), but I haven't bothered to
    # investigate.
    keep_silence = True,
    # "silence" is anything quieter than -30 dBFS.
    silence_thresh = -30,
    # silence must be at least 1000 ms long
    min_silence_len = 1000
)

# Get lengths
for i, chunk in enumerate(chunks):
    print(f"  {i} : {chunk.duration_seconds}")
    # playback.play(chunk)

player = Player(chunks)

print("--------------", end = "\r\n")
print("about to start play", end = "\r\n")
player.play()
print("Started play", end = "\r\n")

t = ''
while t != 'q':
    print('hit any key, q to quit ...')
    t = wait_key()
    p.gotcommand(t)

print("exiting program")
