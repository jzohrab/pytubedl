# open the full file
# audio of first 10 seconds
# vosk it

from pydub import AudioSegment
from pydub import playback
from pydub.silence import split_on_silence
import os
import sys

f = "downloads/test_split.mp3"
print("loading song")
song = AudioSegment.from_mp3(f)
print("making chunk")
duration = 5 * 1000  # ms
chunk = song[:duration]

print("play")
playback.play(chunk)

# OK, chunk can be played no problem
