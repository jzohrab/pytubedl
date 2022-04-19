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
        self.maxindex = len(self.chunks) - 1
        self.index = 0
        self.endindex = len(chunks)
        self.currentindex = 0
        self.is_paused = False

    def printstats(self):
        print(f"player: currindex = {self.currentindex}, index = {self.index}, max = {self.maxindex}")

    def change_index(self, d):
        self.stop()
        i = self.index + d
        if i < 0:
            i = 0
        if i > self.endindex:
            i = self.endindex
        self.index = i
        # self.printstats()
        self.play()
        
    def next(self):
        self.change_index(1)

    def previous(self):
        self.change_index(-1)

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
        self.is_paused = False

    def stop(self):
        self.play_obj.stop()
        self.play_obj = AudioPlayer.null_player

    def is_playing(self):
        return self.play_obj.is_playing()

    def handlekey(self, k):
        print(f"IN PLAYER, got a key: {k}")

    def quit(self):
        print("quitting")
        self.play_obj.stop()
        self.play_obj = AudioPlayer.null_player
        self.index = self.endindex

    def continue_play(self):
        """Ugly method -- keep playing clips if remaining, and if not paused."""
        # print(f"paused = {self.is_paused}; playing = {self.is_playing()}")
        if self.is_paused or self.is_playing():
            return
        self.play()
        self.next()

def playprocessguts(player):
    while player and not player.is_done():
        player.continue_play()


def main():
    chunks = get_chunks()
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
        if (t == 'n'):
            player.next()

    player.quit()

    # Thread must be joined after the player is quit, or it keeps
    # playing to the end.
    thr.join()


if __name__ == "__main__":
   main()
