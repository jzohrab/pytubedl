#!/usr/bin/env python3

# Most of this lifted from https://github.com/alphacep/vosk-api/blob/master/python/example/test_ffmpeg.py
# Must have model in root

from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import os
import wave
import json
import subprocess

def transcribe(filename, showDots=True):
    """Use vosk model to try to make a transcription."""

    if not os.path.exists("model"):
        print ("Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in project root.  See the README")
        exit (1)

    SetLogLevel(-1)
    
    sample_rate=16000
    model = Model("model")
    rec = KaldiRecognizer(model, sample_rate)

    args = [
        'ffmpeg',
        '-loglevel', 'quiet',
        '-i', filename,
        '-ar', str(sample_rate) ,
        '-ac', '1',
        '-f', 's16le',
        '-'
    ]
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    
    while True:
        data = process.stdout.read(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            if showDots:
                print('.', end='', flush=True)
            # print(rec.Result())
            pass
        else:
            if showDots:
                print('.', end='', flush=True)
            # print(rec.PartialResult())
            pass
    
    if showDots:
        print()
        
    result = json.loads(rec.FinalResult())
    return result.get('text')


if __name__ == "__main__":
    filename = sys.argv[1]
    s = transcribe(filename, showDots=True)
    print()
    print(s)
