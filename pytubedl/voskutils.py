from pydub import AudioSegment
from pydub import playback
from pydub.silence import split_on_silence
import os
import sys
from vosk import Model, KaldiRecognizer, SetLogLevel
import wave

# Precondition for vosk.
if not os.path.exists("model"):
    print ("Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
    exit (1)

SetLogLevel(-1)


class TranscriptionCallback(object):
    """Callbacks to report on transcription status."""
    def __init__(self): pass
    def totalbytes(self, t): pass
    def bytesread(self, b): pass
    def partial_result(self, r): pass
    def result(self, r): pass
    def final_result(self, r): pass
    

def transcribe_wav(f, callback):
    """Transcrabe a .wav file, calling back to provide updates.
    ref https://github.com/alphacep/vosk-api/blob/master/python/example/test_simple.py
    """

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

    totalbytes = wf.getnframes() * wf.getsampwidth()
    callback.totalbytes(totalbytes)

    end_of_stream = False
    while not end_of_stream:
        data = wf.readframes(4000)
        callback.bytesread(len(data))

        if len(data) == 0:
            end_of_stream = True
        if rec.AcceptWaveform(data):
            callback.result(rec.Result())
        else:
            callback.partial_result(rec.PartialResult())
    wf.close()

    callback.final_result(rec.FinalResult())


def transcribe_audiosegment(chunk, cb = TranscriptionCallback()):
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
        ret = transcribe_wav(f.name, cb)
    return ret


#############################
# Sample usage with callback.

def main():

    import json

    class ConsoleCallback(TranscriptionCallback):

        def __init__(self):
            super()
            self._totalbytes = 100
            self._bytesread = 0
            self._pct = 0
            self._last_pct = 0
            self.latest_result = None

        def totalbytes(self, t):
            print(f'About to read {t}')
            self._totalbytes = t

        def bytesread(self, b):
            self._bytesread += b
            print('.', end='', flush=True)
            self._pct = int((self._bytesread / self._totalbytes) * 100)
            if self._pct - self._last_pct > 10:
                self.alert_update()
                self._last_pct = self._pct

        def alert_update(self):
            print()
            print(f'{self._pct}%: {self.latest_result}')

        def partial_result(self, r):
            # print(r)
            t = json.loads(r)
            self.latest_result = t.get('partial')

        def result(self, r):
            # print(r)
            t = json.loads(r)
            self.latest_result = t.get('partial')

        def final_result(self, r):
            # print(r)
            t = json.loads(r)
            self.latest_result = t.get('text')
            print()
            print('done')

    f = "downloads/test_split.mp3"
    print("loading song")
    song = AudioSegment.from_mp3(f)
    print("making chunk")
    duration = 5 * 1000  # ms
    chunk = song[:duration]
    c = ConsoleCallback()
    s = transcribe_audiosegment(chunk, c)
    print(c.latest_result)


if __name__ == "__main__":
   main()
