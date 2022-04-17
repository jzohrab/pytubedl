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
import time

class Player:

    def __init__(self, chunks):
        self.chunks = chunks
        self.maxindex = len(self.chunks)
        self.index = 0
        self.thread = None

    def next_thing(self):
        print("called next_thing")
        pass

    def play_chunk(self):
        print(f"playing chunk {self.index} for 2 seconds")
        time.sleep(10)
        print("done playing")

    def play(self):
        # Start current chunk on a thread.
        # Calls back when it's done.
        # ??
        self.thread = threading.Thread(target=self.play_chunk)
        self.thread.start()

    def gotcommand(self, t):
        print("got command : " + t)

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

p = Player(chunks)
print("about to start play")
p.play()
print("Started play")

t = ''
while t != 'q':
    print('hit any key, q to quit ...')
    t = wait_key()
    p.gotcommand(t)

print("exiting program")
