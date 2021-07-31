import sys
import os
from pydub import AudioSegment
from pydub.playback import play
from vosk_transcription import transcribe

if len(sys.argv) < 2:
    print('Missing file argument(s)')
    sys.exit(1)

currfile = sys.argv[1]
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

chain_link_size = 2000

# User will start listening to the clip at position curr_pos, and
# increases curr_pos until it is equal to duration (i.e., is playing
# the entire clip).
curr_pos_ms = min(chain_link_size, duration_ms)

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
    print(f'play from {curr_pos_ms} for {chain_link_size * 2 / 1000} s')
    start = -1 * curr_pos_ms
    end = -1 * curr_pos_ms + (2 * chain_link_size)
    if end >= 0:
        end = -1
    curr = song[start:end]
    play(curr)

def back():
    global curr_pos_ms
    curr_pos_ms += 2000
    curr_pos_ms = min(curr_pos_ms, duration_ms)
    print_cursor()
    play_clip()

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
duration (ms):  {duration_ms}
current (ms):   {curr_pos_ms}
link size (ms): {chain_link_size}
filename:       {currfile}
""")

def unknown():
    print('unknown option')

def noop():
    pass

def print_commands():
    print("""
<nothing>      play clip starting at current position
p              play full clip
l OR n         play current link (start of clip)
< OR , OR b    move back (longer clip)
> OR . OR f    move forward (shorter clip)
i              print info
z OR s         set chain link size
t              print file transcription
q              quit
?              help
""")

def print_transcription():
    s = transcribe(currfile, showDots=True)
    print()
    print(s)

commands = {
    '': play_clip,
    'p': play_full,
    'l': play_link,
    'n': play_link,
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
