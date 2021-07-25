# Python YouTube downloader


# Starting up and shutting down

```
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (some from other git repos, see requirements.txt)
.venv/bin/pip3 install -r requirements.txt

... work work work OR use use use

deactivate
```


## Queue file

Create a queue file with URLs that you want to download, eg, `queue.txt`:

```
## Lines starting with # are ignored

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

