from tube_dl import Youtube, extras
import os
import sys


class YouTubeDownloader:
    """Actual downloader."""

    def download_video(self, url):
        yt = Youtube(url)
        b = yt.formats.first().download()
        return b.file_path

    def download_audio(self, url):
        yt = Youtube(url).formats.filter_by(only_audio=True)[0]
        b = yt.download()
        extras.Convert(b, 'mp3', add_meta=True)
        # *assuming* that the downloaded file is .mp4, bad code
        return b.file_path.replace('.mp4', '.mp3')

class FakeDownloader:
    """Fake downloader for local dev."""
    def writefile(self, fname, url):
        f = open(fname, 'w')
        f.write('Hello to ' + url)
        f.close()
        return fname

    def download_video(self, url):
        return self.writefile('somefile here.mp4', url)

    def download_audio(self, url):
        return self.writefile('somefile here.mp3', url)

print("downloading videos listed in " + str(sys.argv[1]))
f = open(sys.argv[1], "r")
lines = [
    s for s in
    [ s.strip() for s in f.readlines() ]
    if not s.startswith('#') and s != ''
]

saveas = str(sys.argv[2])
if (saveas != 'a' and saveas != 'v'):
    print('\nSpecify saveas a or v\n\n')
    sys.exit(1)

dl = YouTubeDownloader()
env = os.environ.get('ENV')
if (env == 'TEST'):
    print('using fake downloader')
    dl = FakeDownloader()

def filename(title):
    """Convert a title to a usable filename"""
    s = title.replace(' ', '_').replace('"', '').replace('|', '')
    return s

for lin in lines:
    print('downloading ' + lin)
    f = None
    if (saveas == 'a'):
        f = dl.download_audio(lin)
    if (saveas == 'v'):
        f = dl.download_video(lin)
    print('  done')
    dirname, fname = os.path.split(f)
    newpath = os.path.join(dirname, 'downloads', filename(fname))
    os.rename(f, newpath)
    print('  moved to ' + newpath)
