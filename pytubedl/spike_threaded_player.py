# open the full file
# audio of first 10 seconds
# vosk it

import collections
import multiprocessing as mp
import os
import simpleaudio
import sys
import threading
import time

from console.utils import wait_key
from multiprocessing import Process, Queue
from pydub import AudioSegment
from pydub import playback
from pydub.silence import split_on_silence

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

        handler = getattr(self, event, None)
        if not handler:
            raise NotImplementedError("Process has no handler named [%s]" % event)

        handler(*args)

    def run(self):
        while not self.is_closed:
            msg = self.queue.get()
            self.dispatch(msg)


class Player(BaseProcess):

    def __init__(self, chunks):
        super().__init__()
        # self._closed = False
        self.proc = None
        self.play_obj = None
        self.chunks = chunks
        self.maxindex = len(self.chunks)
        self.index = 0

    def play_chunk(self):
        print(f"  playing  {self.index}", end = "\r\n")
        seg = self.chunks[self.index]
        # playback.play(chunk) - old

        # Using simpleaudio directly, as suggested in https://github.com/jiaaro/pydub/issues/572
        self.play_obj = simpleaudio.play_buffer(
            seg.raw_data,
            num_channels=seg.channels,
            bytes_per_sample=seg.sample_width,
            sample_rate=seg.frame_rate
        )
        self.play_obj.wait_done()

        print(f"  finished {self.index}", end = "\r\n")

    def do_play(self):
        # Start current chunk on a thread.
        # Calls back when it's done.
        # ??
        i = self.index
        print(f"called play with index = {i}", end = "\r\n")
        # self.play_chunk()

        # Start playing chunk in a process, so we can control it.
        pp = Process(target=self.play_chunk)
        self.proc = pp
        print(f"in do_play: got a self.proc? {self.proc is not None}")
        self.proc.start()
        self.proc.join()
        print(f"in do_play: after join(), still got a self.proc? {self.proc is not None}")

        if (self.index < self.maxindex - 1):
            # self.do_play()
            self.index += 1
            self.send('do_play')
        else:
            print("No more chunks.", end = "\r\n")
            # DON'T necessarily quit ... the user might want to backtrack, export the last clip, etc.  Just hang out.
            # self.send('do_quit')

        print(f"end of call to play with index {i}", end = "\r\n")

    def do_quit(self):
        self.is_closed = True
        print(f"quitting, perhaps need to wait", end = "\r\n")
        self.queue.close()
        print(f"done quitting", end = "\r\n")
        # self.queue.join()

    def previous(self):
        print(f"Going back to previous, current index = {self.index}")
        ci = self.index
        ci -= 1
        if (ci < 0):
            ci = 0
        self.index = ci

    def quit(self):
        if (self.play_obj is not None):
            print("stopping play obj")
            self.play_obj.stop()
        else:
            print("no play_obj to stop")

        if (self.proc is not None):
            print("- terminating proc right away", end = "\r\n")
            self.proc.terminate()
        else:
            print("no proc to terminate", end = "\r\n")
        self.send('do_quit')

    def printstats(self):
        print(f"- Curr index: {self.index}.  count: {self.maxindex}.  Got self.proc? {self.proc is not None}")


######################
# Getting chunks

def get_chunks():

    f = "sample/ten_seconds.mp3"
    print("loading song")
    song = AudioSegment.from_mp3(f)
    
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

################

def main():
    # chunks = ['apple', 'bat', 'cat', 'dog']
    chunks = get_chunks()

    player = Player(chunks)

    print("--------------", end = "\r\n")
    print("about to start()", end = "\r\n")
    player.start()
    print("done start()", end = "\r\n")

    print("--------------", end = "\r\n")
    print("about to send 'play'", end = "\r\n")
    # player.play()
    player.send('do_play')
    print("sent 'play'", end = "\r\n")

    t = ''
    while (t != 'q'):
        print('hit any key, q to quit ...')
        t = wait_key()
        print(f"Got a key: {t}")
        if (t == 'a'):
            player.previous()
        if (t == 'p'):
            player.printstats()

    player.quit()

    print("exiting program ...")


######################
# Main

# Have to do this "__name__ == __main__" check,
# or python complains with:
# An attempt has been made to start a new process before the current process has finished its bootstrapping phase.
# if __name__ == "__main__":
#    main()
#    # mainProcessPlayer()


####
# even easier?
# ref https://stackoverflow.com/questions/58566079/how-do-i-stop-simpleaudio-from-playing-a-file-twice-simulaneously


class AudioPlayer:
    def __init__(self, chunks):
        self.play_obj = None
        self.chunks = chunks
        self.maxindex = len(self.chunks) - 1
        self.index = -1
        self.endindex = len(chunks)
        self.is_paused = False

    def printstats(self):
        print(f"player: index = {self.index}, max = {self.maxindex}")

    def next(self):
        i = self.index + 1
        if i > self.endindex:
            i = self.endindex
        self.index = i
        self.printstats()

    def previous(self):
        i = self.index - 1
        if i < 0:
            i = 0
        self.index = i
        self.printstats()

    def is_done(self):
        return self.index >= self.endindex

    def toggle_pause(self):
        p = self.is_paused
        now_paused = not p
        if now_paused:
            self.play_obj.stop()
        else:
            self.play()
        self.is_paused = now_paused

    def play(self):
        if (self.is_done()):
            return

        print(f"Playing index {self.index}")
        seg = self.chunks[self.index]

        # Using simpleaudio directly, as suggested in https://github.com/jiaaro/pydub/issues/572.
        #
        # per simpleaudio docs, noted in https://stackoverflow.com/questions/58566079/how-do-i-stop-simpleaudio-from-playing-a-file-twice-simulaneously,
        #
        # The module implements an asynchronous interface, meaning
        # that program execution continues immediately after audio
        # playback is started and a background thread takes care of
        # the rest. This makes it easy to incorporate audio playback
        # into GUI-driven applications that need to remain responsive.
        self.play_obj = simpleaudio.play_buffer(
            seg.raw_data,
            num_channels=seg.channels,
            bytes_per_sample=seg.sample_width,
            sample_rate=seg.frame_rate
        )


    def is_playing(self):
        if self.play_obj:
                return self.play_obj.is_playing()
        return False

    def handlekey(self, k):
        print(f"IN PLAYER, got a key: {k}")

    def quit(self):
        print("quitting")
        if self.play_obj:
            self.play_obj.stop()
        self.index = self.endindex

    def continue_play(self):
        """Ugly method -- keep playing clips if remaining, and if not paused."""
        if self.is_paused or self.is_playing():
            return

        self.next()
        if not self.is_done():
            self.play()


def playprocessguts(player):
    while not player.is_done():
        player.continue_play()


def main2():
    # chunks = ['apple', 'bat', 'cat', 'dog']
    chunks = get_chunks()
    # p = Process(target=playprocessguts, args=(chunks,))
    # p.start()
    player = AudioPlayer(chunks)
    thr = threading.Thread(target=playprocessguts, args=(player,))
    thr.start()

    t = ''
    while (t != 'q'):
        print('hit any key, q to quit ...')
        t = wait_key()
        if (t == ' '):
            player.toggle_pause()
        if (t == 'p'):
            player.previous()

    player.quit()

    # p.join()
    thr.join()


if __name__ == "__main__":
   main2()
   # mainProcessPlayer()
