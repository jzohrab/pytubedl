# Borrowed mostly from
# https://stackoverflow.com/questions/45526996/split-audio-files-using-silence-detection

# Import the AudioSegment class for processing audio and the 
# split_on_silence function for separating out silent chunks.
from pydub import AudioSegment
from pydub.silence import split_on_silence
import os
import sys

# Normalize a chunk to a target amplitude.
def match_target_amplitude(aChunk, target_dBFS):
    ''' Normalize given audio chunk '''
    change_in_dBFS = target_dBFS - aChunk.dBFS
    return aChunk.apply_gain(change_in_dBFS)

# String padding
# (hack, can't remember built-in function and have no internet ...)
def padleft(n, padlen = 4):
    s = str(n)
    if len(s) > padlen:
        return s
    p = '0' * padlen + s
    return p[-padlen:]

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

# Put chunks in dir under file
dirname = f.replace('.mp3', '')
os.mkdir(dirname)

# Load your audio.
print('loading song ...')
song = AudioSegment.from_mp3(f)

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
    min_silence_len = 500
)


# Create a silence chunk that's 0.5 seconds (or 500 ms) long for padding.
silence_chunk = AudioSegment.silent(duration=500)

# Process each chunk
print('Creating files ...')
maxlen = len(str(len(chunks)))
for i, chunk in enumerate(chunks):
    # Add the padding chunk to beginning and end of the entire chunk.
    audio_chunk = silence_chunk + chunk + silence_chunk

    # Normalize the entire chunk.
    normalized_chunk = match_target_amplitude(audio_chunk, -20.0)

    # Export the audio chunk with new bitrate.
    fname = "chunk_{0}.mp3".format(padleft(i + 1, maxlen))
    print(f"  {fname} (of {len(chunks)})")
    normalized_chunk.export(
        os.path.join(dirname, fname),
        bitrate = "192k",
        format = "mp3"
    )
