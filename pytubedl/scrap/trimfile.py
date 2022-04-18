# Trim an existing file only.

# Import the AudioSegment class for processing audio and the 
# split_on_silence function for separating out silent chunks.
from pydub import AudioSegment
import os
import sys

# Get file to split.
f = str(sys.argv[1])
errmsg = None
if f is None:
    errmsg = 'Missing file argument'
if not os.path.exists(f):
    errmsg = ('Missing file ' + f)
if not f.endswith('.mp3'):
    errmsg = 'File must be .mp3'
if errmsg:
    print(errmsg)
    sys.exit(1)

# Load your audio.
print('loading song ...')
song = AudioSegment.from_mp3(f)

duration = 10 * 1000  # ms
song = song[:duration]

fname = "ten_seconds.mp3"
song.export(
    fname,
    bitrate = "192k",
    format = "mp3"
)
