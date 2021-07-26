# Python YouTube downloader and backchainer

Download youtube files, and after breaking them up, use backchaining to work on sentence pronunciation.

# Dependencies

python3
ffmpeg
For mac: `brew install ffmpeg`

# Starting up and shutting down

```
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (some from other git repos, see requirements.txt)
.venv/bin/pip3 install -r requirements.txt

... work work work OR use use use

deactivate
```

# Downloading videos

Useful when you need to go offline, or just save bandwidth.

## Queue file

Create a queue file with YouTube URLs that you want to download, eg, `queue.txt` (lines starting with # are ignored):

```
# Jorge B ansiedad meditacion
https://www.youtube.com/watch?v=cgvR03wrolY

# Wim Hof guided breathing
https://www.youtube.com/watch?v=tybOi4hjZFQ
```

## Usage / Sample call

```
python3 pytubedl/download.py <queue file> [a|v]
```

'a' or 'v' for audio or video, e.g.:

```
python3 pytubedl/download.py queue.txt a
```

Audio is downloaded, and videos are stored in the "downloads" subfolder.

## Development (faking downloads)

Set `ENV=TEST` to use a fake downloader, e.g:

```
ENV=TEST python3 pytubedl/download.py queue.txt a
```

# Backchaining

Given a short audio file, play a small piece at the end, then gradually build on top of that.

```
python3 pytubedl/backchain.py ~/Downloads/hack-01.mp3
```

Command-line-only, it's all work-in-progress.