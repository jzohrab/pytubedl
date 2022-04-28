# Clip maker

TODO update this.  include:

* vosk model
* config.ini
* install and running
* ankiconnect


TODO list

```
# MVP TODO (usable for me)

# - popup: re-styling of form: graph at top, slider under that, buttons under that
# - popup: "status label" for feedback - export start/stop, transcribe fail, transcribe done
# - popup hotkeys
# - restyle main screen:
#   - slider at top, then slider buttons, then bookmark list, then bk buttons
# - can't change bookmark pos for <Full Track>"
# - can't add "end clip" for <Full Track>
# - export clipped mp3 file to disk
# - better error handling for failed transcription model
# - list hotkeys in README
# - any other TODOs in the code.
# - remove dev hack
# - remove 'q' quit shortcut on main
# - move files to new repo
# - minimal requirements.txt
# - split classes to separate files
# - fresh checkout, install, build from scratch in new venv

# - packaging?

# Future TODOs:
# - hotkey help - https://mail.python.org/pipermail/python-list/2003-April/229647.html
# - configurable anki save destination
# - "save" and "import" to load all bookmarks and stuff
# - maybe "add note" to bookmark?
# - clip editor popup:
#   - add double slider https://github.com/MenxLi/tkSliderWidget?
#   - respect double slider on playback
#   - add buttons to reposition the start and end of the slider values, respecting max
#   - resave/replace
```


# Python backchainer

Utils to break up an audio file, and use backchaining to work on sentence pronunciation.

This uses [Vosk](https://github.com/alphacep/vosk-api) for offline audio transcription.  You have to install a model for the language you want (see https://alphacephei.com/vosk/models) -- unfortunately only a few languages are supported at the moment.

# Dependencies

* python3
* ffmpeg (For mac: `brew install ffmpeg`)
* vosk model (see below for spanish)

```
# Spanish - this must be installed in a directory called 'model' in the project root.
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.3.zip
unzip vosk-model-small-es-0.3.zip 
mv vosk-model-small-es-0.3 model
```

# TODO - some sort-of-polishing

General idea:

* given an audio file
* load it, split it into chunks, not writing individual files out b/c that takes time
* configurable params: min chunk length, min db, silence length
* start loop, similar to existing backchaining loop.

Loop:

* play current chunk
* r replays current
* n = move to next, and play it (return does the same)
* p = move to prev and play it
* j = join current chunk w/ previous
* u = "unjoin" current chunk into components
* x = export current chunk and transcription to AnkiConnect
* t = transcribe

* b = enter backchaining sub-loop, similar to existing thing


# Starting up and shutting down

```
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (some from other git repos, see requirements.txt)
.venv/bin/pip3 install -r requirements.txt

... work work work OR use use use

deactivate
```

# Split a file into chunks

Use `splitaudio.py`, e.g.:

```
python pytubedl/splitaudio.py path/to/your.mp3
```

This creates `chunk_00x.mp3` files in a subdirectory with the same name as the file (e.g., `path/to/your/chunk_001.mp3`).

# Backchaining

Given a short audio file, play a small piece at the end, then gradually build on top of that.

```
python3 pytubedl/backchain.py ~/Downloads/hack-01.mp3
```

Command-line-only, it's all work-in-progress.

