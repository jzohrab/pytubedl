# open the full file
# audio of first 10 seconds
# vosk it

from pydub import AudioSegment
from pydub import playback
from pydub.silence import split_on_silence
import os
import sys

# Precondition for vosk.
if not os.path.exists("model"):
    print ("Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
    exit (1)


######################
# Vosk transcribe a wav file.
# Copied from below URL:
# https://github.com/alphacep/vosk-api/blob/master/python/example/test_simple.py

from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import os
import wave
import json

SetLogLevel(-1)

def transcribe_wav(f):
    wf = wave.open(f, "rb")
    # print(f"channels: {wf.getnchannels()}")
    # print(f"width: {wf.getsampwidth()}")
    # print(f"comp type: {wf.getcomptype()}")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        print ("Audio file must be WAV format mono PCM.")
        wf.close()
        exit (1)

    model = Model("model")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    # rec.SetPartialWords(True)

    while True:
        data = wf.readframes(4000)
        print('.', end='', flush=True)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)
        # if rec.AcceptWaveform(data):
        #     print(rec.Result())
        # else:
        #     print(rec.PartialResult())
    wf.close()

    print()
    result = json.loads(rec.FinalResult())
    return result.get('text')


def transcribe_audiosegment(chunk):
    # Per https://github.com/jiaaro/pydub/blob/master/pydub/playback.py,
    # playback falls back to ffplay, so we'll assume that's what's being used.
    # In this case, pydub actually dumps content to a temp .wav file, and
    # then plays with that.
    # Since that's how we're playing it, just use that for vosk as well.
    ret = ''
    chunk = chunk.set_channels(1)
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile("w+b", suffix=".wav") as f:
        chunk.export(f.name, format='wav')
        ret = transcribe_wav(f.name)
    return ret


######################
# Main

def main():
    f = "downloads/test_split.mp3"
    print("loading song")
    song = AudioSegment.from_mp3(f)
    print("making chunk")
    duration = 5 * 1000  # ms
    chunk = song[:duration]
    s = transcribe_audiosegment(chunk)
    print(s)


if __name__ == "__main__":
   main()
