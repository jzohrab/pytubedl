import sys
import os
from pydub import AudioSegment
from pydub.playback import play
from vosk_transcription import transcribe
import math

if len(sys.argv) < 2:
    print('Missing file argument(s)')
    sys.exit(1)

files = sys.argv[1:]
currfilenum = 0
currfile = None
song = None
duration_ms = 0
chain_link_size = 2000
curr_pos_ms = 0

def load_curr_song():
    global song
    global duration_ms
    global currfile
    global curr_pos_ms
    currfile = files[currfilenum]
    errmsg = None
    if currfile is None:
        errmsg = 'Missing file argument'
    if not os.path.exists(currfile):
        errmsg = ('Missing file ' + currfile)
    if not currfile.endswith('.mp3'):
        errmsg = 'File must be .mp3'
    if errmsg:
        print(errmsg)
        sys.exit(1)

    song = AudioSegment.from_mp3(currfile)
    duration_ms = song.duration_seconds * 1000

    # User will start listening to the clip at position curr_pos, and
    # increases curr_pos until it is equal to duration (i.e., is playing
    # the entire clip).
    curr_pos_ms = min(chain_link_size, duration_ms)

def next_song():
    global currfilenum
    currfilenum += 1
    if currfilenum > (len(files) + 1):
        print("All done.")
        sys.exit(0)
    load_curr_song()
    play(song)

def print_cursor():
    print(f"{curr_pos_ms / 1000} of {duration_ms / 1000}")

def play_clip():
    print(f'play from {curr_pos_ms}')
    start = -1 * curr_pos_ms
    curr = song[start:]
    play(curr)

def play_full():
    print('play full')
    play(song)

def play_link():
    print(f'play from {curr_pos_ms} for {chain_link_size * 1.5 / 1000} s')
    start = -1 * curr_pos_ms
    end = -1 * curr_pos_ms + math.floor(1.5 * chain_link_size)
    if end >= 0:
        end = -1
    curr = song[start:end]
    play(curr)

def back():
    global curr_pos_ms
    curr_pos_ms += 2000
    curr_pos_ms = min(curr_pos_ms, duration_ms)
    print_cursor()
    play_link()

def set_link_size():
    """Set the size of the increment.  Not doing much error handling,
    sensibility checks, etc, it's up to the user to set things correctly."""
    global chain_link_size
    new_size = input('Enter link size (ms): ')
    try:
        new_size = int(new_size)
    except:
        print('bad entry, setting to 2000')
        new_size = 2000
    new_size = max(250, new_size)
    new_size = min(5000, new_size)  # assuming not a mentat
    chain_link_size = new_size
    print(f'Chain link size set to {chain_link_size}')
    
def forward():
    global curr_pos_ms
    curr_pos_ms -= 2000
    curr_pos_ms = max(0, curr_pos_ms)
    print_cursor()
    play_clip()

def print_stats():
    print(f"""
file:           {currfile}
duration (ms):  {duration_ms}
current (ms):   {curr_pos_ms}
""")

def unknown():
    print('unknown option')

def noop():
    pass

def print_commands():
    print("""
<nothing>      play clip starting at current position
r              replay full clip
l              play current link (start of clip)
< OR , OR b    move back (longer chain)
> OR . OR f    move forward (shorter chain)
i              print info
z OR s         set chain link size
t              print clip transcription
n              move to next clip
q              quit
?              help
""")

def print_transcription():
    s = transcribe(currfile, showDots=True)
    print()
    print(s)

commands = {
    '': play_clip,
    'r': play_full,
    'l': play_link,
    'n': next_song,
    '<': back,
    ',': back,
    'b': back,
    '>': forward,
    '.': forward,
    'f': forward,
    'i': print_stats,
    'z': set_link_size,
    's': set_link_size,
    '?': print_commands,
    't': print_transcription,
    'q': noop
}

######
# Main

load_curr_song()

print_commands()

# User enters command
userchoice = 'i'
while userchoice != 'q':
    userchoice = input('Enter command: ').strip()
    command = commands.get(userchoice, unknown)
    command()

sys.exit(0)

a = 2000
start = -1 * a
curr = song[start:]

play(curr)
