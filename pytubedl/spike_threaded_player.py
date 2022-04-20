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

    def __init__(self, chunks):
        self.play_obj = None # AudioPlayer.null_player
        self.chunks = chunks
        self.endindex = len(chunks)

        # Index used by the player.
        self.index = 0
        # Index of what's currently being played, necessary to resolve some threading issues.
        self.currently_playing_index = 0

        # For "auto-advance" playing.
        self.autoplaythread = None

    def printstats(self):
        print(f"player: index = {self.index}")

    def change_index(self, d):
        """Move to next or previous."""
        self._stopplaying()
        i = self.index + d
        if i < 0:
            i = 0
        if i > self.endindex:
            i = self.endindex
            # Stop the "autoplay" thread.
            # self.stop()
        self.index = i
        
    def next(self):
        self.change_index(1)

    def previous(self):
        self.change_index(-1)

    def is_done(self):
        return self.index >= self.endindex

    def play_current(self):
        """Play chunk at current index only."""
        if (self.is_playing() or self.is_done()):
            # print("fast exit of play_current")
            return

        i = self.index
        seg = self.chunks[i]
        self.play_obj = simpleaudio.play_buffer(
            seg.raw_data,
            num_channels=seg.channels,
            bytes_per_sample=seg.sample_width,
            sample_rate=seg.frame_rate
        )

        # Hacky_thread_code: Keep track of the actual playing index.
        # The _autoplay thread changes self.index, and it misbehaves
        # from the user's perspective if the user tries to "move
        # next/previous" while autoplay is occurring.
        self.currently_playing_index = i

        self.play_obj.wait_done()

    def _autoplay(self):
        if (self.autoplaythread is None):
            return
        while not self.autoplaythread.stopped() and not self.is_done():
            if not self.is_playing():
                self.play_current()
                # print("in _autoplay, moving to next")

                # Hacky_thread_code: If the currently playing index is
                # the same as the player's index, the user hasn't
                # requested a move previous/next, so just move to the
                # next one.
                if (self.currently_playing_index == self.index):
                    i = self.index + 1
                    if i > self.endindex:
                        i = self.endindex
                    self.index = i

                # self.next()
            # time.sleep(0.05) # 50 ms

    def play(self):
        self.autoplaythread = StoppableThread(target=self._autoplay)
        self.autoplaythread.start()

    def _stopplaying(self):
        if self.play_obj is not None:
            self.play_obj.stop()
            # self.play_obj = AudioPlayer.null_player
            self.play_obj = None

    def stop(self):
        self._stopplaying()

        # Hacky_thread_code: Setting currently_playing_index to None
        # means that when the _autoplay resumes, it doesn't restart on
        # the next index.
        self.currently_playing_index = None
        if (self.autoplaythread is not None and self.autoplaythread.is_alive()):
            self.autoplaythread.stop()

    def is_playing(self):
        if self.play_obj is None: return False
        return self.play_obj.is_playing()

    def quit(self):
        # print("quitting")
        if self.play_obj is not None:
            self.play_obj.stop()
            self.play_obj = None # AudioPlayer.null_player
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
            print("p hit, moving previous")
            player.previous()
        if (t == 'n'):
            player.next()

    player.quit()


if __name__ == "__main__":
   main()
