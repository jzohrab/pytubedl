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


####
# ref https://stackoverflow.com/questions/58566079/how-do-i-stop-simpleaudio-from-playing-a-file-twice-simulaneously

# From https://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread/
class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""
    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()



class AudioPlayer:

    # A "NullPlayer" implementing the interface of the object returned by simpleaudio.play_buffer,
    # which does nothing.
    class NullPlayer:
        def stop(self): pass
        def play_buffer(self): pass
        def is_playing(self): return False

    null_player = NullPlayer()

    def __init__(self, chunks):
        self.play_obj = AudioPlayer.null_player
        self.chunks = chunks
        self.endindex = len(chunks)

        # NOTE we start "before" the first track ... calling play()
        # advances the index to 0, to the first track.
        self.index = -1
        self.currentindex = self.index
        self.is_autoplay = False

        # For "auto-advance" playing.
        self.autoplaythread = None

    def printstats(self):
        print(f"player: currindex = {self.currentindex}, index = {self.index}")

    def change_index(self, d):
        """Move to next or previous."""
        self._stopplaying()
        i = self.currentindex + d
        if i < 0:
            i = 0
        if i > self.endindex:
            i = self.endindex
            self.stop()
        self.index = i
        self.printstats()
        # self.play_current()
        
    def next(self):
        self.change_index(1)

    def previous(self):
        self.change_index(-1)

    def is_done(self):
        return self.index >= self.endindex

    def play_current(self):
        """Play chunk at current index only."""
        if (self.is_playing()):
            return
        if (self.is_done()):
            return

        self.currentindex = self.index
        # print(f"Playing index {self.currentindex}")
        seg = self.chunks[self.currentindex]

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

    def _autoplay(self):
        if (self.autoplaythread is None):
            return
        while not self.autoplaythread.stopped() and not self.is_done():
            if not self.is_playing():
                self.next()
                self.play_current()
            time.sleep(0.05) # 50 ms

    def play(self):
        self.autoplaythread = StoppableThread(target=self._autoplay)
        self.autoplaythread.start()

    def _stopplaying(self):
        self.play_obj.stop()
        self.play_obj = AudioPlayer.null_player

    def stop(self):
        self._stopplaying()
        if (self.autoplaythread.is_alive()):
            self.autoplaythread.stop()

    def is_playing(self):
        return self.play_obj.is_playing()

    def handlekey(self, k):
        print(f"IN PLAYER, got a key: {k}")

    def quit(self):
        print("quitting")
        self.play_obj.stop()
        self.play_obj = AudioPlayer.null_player
        self.index = self.endindex



def main():
    chunks = get_chunks()
    player = AudioPlayer(chunks)
    player.play()

    t = ''
    while (t != 'q'):
        print('hit any key, q to quit ...')
        t = wait_key()
        if (t == ' '):
            print(f"playing? {player.is_playing()}")
            if player.is_playing():
                player.stop()
            else:
                print("restarting")
                player.play()
        if (t == 'p'):
            player.previous()
        if (t == 'n'):
            player.next()

    player.quit()


if __name__ == "__main__":
   main()
