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


import multiprocessing as mp
import collections

Msg = collections.namedtuple('Msg', ['event', 'args'])

# Stolen from https://stackoverflow.com/questions/11515944/how-to-use-multiprocessing-queue-in-python
class BaseProcess(mp.Process):
    """A process backed by an internal queue for simple one-way message passing.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = mp.Queue()
        self.is_closed = False

    def send(self, event, *args):
        """Puts the event and args as a `Msg` on the queue
        """
        msg = Msg(event, args)
        self.queue.put(msg)

    def dispatch(self, msg):
        event, args = msg

        handler = getattr(self, "do_%s" % event, None)
        if not handler:
            raise NotImplementedError("Process has no handler for [%s]" % event)

        handler(*args)

    def run(self):
        while not self.is_closed:
            msg = self.queue.get()
            self.dispatch(msg)


class Player(BaseProcess):

    def __init__(self, chunks):
        super().__init__()
        # self._closed = False
        self.chunks = chunks
        self.maxindex = len(self.chunks)
        self.index = 0
        self.proc = None

    def next_thing(self):
        print("called next_thing", end = "\r\n")
        pass

    def play_chunk(self):
        print(f"  playing  {self.index}", end = "\r\n")
        time.sleep(2)
        print(f"  finished {self.index}", end = "\r\n")
        if (self.index < self.maxindex - 1):
            # self.do_play()
            self.index += 1
            self.send('play')
        else:
            print("No more chunks.", end = "\r\n")
            # DON'T necessarily quit ... the user might want to backtrack, export the last clip, etc.  Just hang out.
            # self.send('quit')

    def do_play(self):
        # Start current chunk on a thread.
        # Calls back when it's done.
        # ??
        i = self.index
        print(f"called play with index = {i}", end = "\r\n")
        self.play_chunk()
        # p = Process(target=self.play_chunk)
        # p.daemon = True
        # self.proc = p
        # self.proc.start()
        print(f"end of call to play with index {i}", end = "\r\n")

    def do_quit(self):
        self.is_closed = True
        print(f"quitting, perhaps need to wait", end = "\r\n")
        self.queue.close()
        print(f"done quitting", end = "\r\n")
        # self.queue.join()

    def gotcommand(self, t):
        print("got command : " + t, end = "\r\n")
        if (t == 'q'):
            if (self.proc is not None):
                self.proc.terminate()
            self.send('quit')


######################
# Getting chunks later

def get_chunks():

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

    return chunks

######################
# Main

def main():
    chunks = [1,2,3,4,5]

    player = Player(chunks)
    player.start()

    print("--------------", end = "\r\n")
    print("about to start play", end = "\r\n")
    # player.play()
    player.send('play')
    print("Started play", end = "\r\n")

    t = ''
    while t != 'q':
        print('hit any key, q to quit ...')
        t = wait_key()
        player.gotcommand(t)

    print("exiting program ...")


# Have to do this "__name__ == __main__" check,
# or python complains with:
# An attempt has been made to start a new process before the current process has finished its bootstrapping phase.
if __name__ == "__main__":
    main()

