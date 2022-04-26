#####
# Clip player
#
# TODO:
# - popup:
"""
- set start and end of clip
- display start/end of clip in list box (display())
- if bookmark already has start/end defined, use that to determine slider from/to, and double-slide
- open form with bookmark with start and end
- transcribe clip
- save transcription etc

- future work:
- add double slider https://github.com/MenxLi/tkSliderWidget?
- respect double slider on playback
- add buttons to reposition the start and end of the slider values, respecting max
- resave/replace
"""
# - "save" and "import" to load all bookmarks and stuff

# - maybe "add note" to bookmark?
# - can't change bookmark pos for <Full Track>"
# - can't add "end clip" for <Full Track>
# - transcribe clip w/ vosk
# - export clipped mp3 file to disk
# - export card and transcription to anki
#
# - any other TODOs in the code.
###

import numpy as np
import tkinter.ttk as ttk
import wave

from enum import Enum
from matplotlib import pyplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mutagen.mp3 import MP3
from pydub import AudioSegment
from pygame import mixer
from tempfile import NamedTemporaryFile
from tkinter import *
from tkinter import filedialog


class TimeUtils:

    @staticmethod
    def time_string(ms):
        total_seconds = ms / 1000.0
        mins = int(total_seconds) // 60
        secs = total_seconds % 60
        return '{:02d}m{:04.1f}s'.format(mins, secs)


class MusicPlayer:
    """Actually plays music, with slider."""

    class State(Enum):
        NEW = 0
        LOADED = 1
        PLAYING = 2
        PAUSED = 3

    def __init__(self, slider, slider_lbl, state_change_callback = None):
        self.slider = slider
        self.slider_lbl = slider_lbl
        self.state_change_callback = state_change_callback

        self.state = MusicPlayer.State.NEW
        self.music_file = None
        self.song_length_ms = 0

        # start_pos_ms is set when the slider is manually
        # repositioned.
        self.start_pos_ms = 0

        self.slider_update_id = None

        self.slider.bind('<Button-1>', self.slider_click)
        self.slider.bind('<ButtonRelease-1>', self.slider_unclick)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, s):
        self._state = s
        if self.state_change_callback:
            self.state_change_callback(s)

    def increment(self, i):
        self.reposition(float(self.slider.get()) + i)

    def slider_click(self, event):
        """User is dragging the slider now, so don't update it."""
        # print('got a slider click')
        self.cancel_slider_updates()

    def slider_unclick(self, event):
        # print('got a slider UNclick')
        value_ms_f = float(self.slider.get())
        self.reposition(value_ms_f)

    def reposition(self, value_ms_f):
        v = value_ms_f
        if (v < 0):
            v = 0
        elif (v > self.song_length_ms):
            v = self.song_length_ms

        self.start_pos_ms = v

        mixer.music.play(loops = 0, start = (v / 1000.0))
        if self.state is not MusicPlayer.State.PLAYING:
            mixer.music.pause()
        self.update_slider()

    def cancel_slider_updates(self):
        if self.slider_update_id:
            self.slider.after_cancel(self.slider_update_id)

    def update_slider(self):
        current_pos_ms = mixer.music.get_pos()
        slider_pos = self.start_pos_ms + current_pos_ms
        if (current_pos_ms == -1 or slider_pos > self.song_length_ms):
            # Mixer.music goes to -1 when it reaches the end of the file.
            slider_pos = self.song_length_ms

        self.slider.set(slider_pos)
        self.slider_lbl.configure(text=TimeUtils.time_string(slider_pos))

        if self.state is MusicPlayer.State.PLAYING:
            if slider_pos < self.slider.cget('to'):
                old_update_id = self.slider_update_id
                self.slider_update_id = self.slider.after(50, self.update_slider)
            else:
                # Reached the end of the slider, stop updating.
                self._pause()

    def load_song(self, f, sl):
        self.stop()
        self.music_file = f
        self.song_length_ms = sl
        mixer.music.load(f)
        self.start_pos_ms = 0.0
        self.state = MusicPlayer.State.LOADED

    def play_pause(self):
        self.cancel_slider_updates()
        if self.music_file is None:
            return

        if self.state is MusicPlayer.State.LOADED:
            # First play, load and start.
            mixer.music.play(loops = 0, start = (self.start_pos_ms / 1000.0))
            self.state = MusicPlayer.State.PLAYING
            # self.start_pos_ms = 0
            self.update_slider()

        elif self.state is MusicPlayer.State.PLAYING:
            self._pause()

        elif self.state is MusicPlayer.State.PAUSED:
            mixer.music.unpause()
            self.state = MusicPlayer.State.PLAYING
            self.update_slider()

        else:
            # Should never get here, but in case I missed something ...
            raise RuntimeError(f'??? weird state {self.state}?')

    def _pause(self):
        mixer.music.pause()
        self.cancel_slider_updates()
        self.state = MusicPlayer.State.PAUSED

    def stop(self):
        self.state = MusicPlayer.State.LOADED
        mixer.music.stop()
        self.cancel_slider_updates()


class BookmarkWindow(object):

    def __init__(self, parent, bookmark, music_file, song_length_ms):
        # The "return value" of the dialog,
        # entered by user in self.entry Entry box.
        self.bookmark = bookmark
        self.music_file = music_file
        self.song_length_ms = song_length_ms

        self.root=Toplevel(parent)
        self.root.protocol('WM_DELETE_WINDOW', self.ok)
        self.root.geometry('700x600')

        clip_frame = Frame(self.root)
        self.slider_min_lbl = Label(clip_frame, text=TimeUtils.time_string(0))
        self.slider_min_lbl.grid(row=1, column=1, pady=2)
        self.slider_max_lbl = Label(clip_frame, text=TimeUtils.time_string(1000))
        self.slider_max_lbl.grid(row=1, column=2, pady=2)
        clip_frame.grid(row=0, column=0, pady=20)

        ctl_frame = Frame(self.root)
        ctl_frame.grid(row=1, column=0, pady=20)

        self.entry = Entry(ctl_frame)
        self.entry.insert(END, bookmark.position_ms)
        self.entry.grid(row=0, column=1, padx=10)
        f = ('Times', 10)
        self.play_btn = Button(ctl_frame, text='Play', width=10, font=f, command=self.play_pause)
        self.play_btn.grid(row=0, column=2, padx=10)
        self.ok_btn = Button(ctl_frame, text="ok", command=self.ok)
        self.ok_btn.grid(row=0, column=3, padx=10)

        # For bookmark, assume that the user clicked "bookmark"
        # *after* hearing something interesting -- so pad a bit more
        # before than after.
        # self.from_val and to_val are also used during plotting.
        pad_before = 10 * 1000
        pad_after = 5 * 1000
        self.from_val = int(max(0, bookmark.position_ms - pad_before))
        self.to_val = int(min(self.song_length_ms, bookmark.position_ms + pad_after))

        slider_frame = Frame(self.root)
        slider_frame.grid(row=2, column=0, pady=20)

        # Note: I tried using ttk.scale for better styling, but it was
        # garbage.  The slider handle kept jumping out of the scale,
        # and not respecting the from_ and to values of the scale
        # (e.g., for from_=2500 and to=4500, a value of 3500 (right in
        # the middle) would be shown about 75% along the scale, and
        # for higher values it would disappear completely).
        #
        # ref https://stackoverflow.com/questions/71994893/
        #   tkinter-ttk-scale-seems-broken-if-from-is-not-zero-mac-python-3-8-2-tcl-tk
        #
        # Slider length had to be eyeballed here, as the matplotlib
        # size is specified in inches.  I wasn't sure how to align the
        # sizes easily.
        sllen = 5 * 60
        self.slider = Scale(
            slider_frame,
            from_=self.from_val,
            to=self.to_val,
            orient=HORIZONTAL,
            sliderlength = 10,
            length= sllen)
        self.slider.grid(row=1, column=0, pady=10)
        self.slider_lbl = Label(slider_frame, text='')
        self.slider_lbl.grid(row=2, column=0, pady=2)

        self.slider_frame = slider_frame
        self.signal_plot_data = self.get_signal_plot_data(self.from_val, self.to_val)
        self.plot()

        self.clip_slider = Scale(
            slider_frame,
            from_=self.from_val,
            to=self.to_val,
            orient=HORIZONTAL,
            length= sllen)
        self.clip_slider.grid(row=4, column=0, pady=10)
        self.clip_slider.bind('<Button-1>', self.clip_slider_click)
        self.clip_slider.bind('<ButtonRelease-1>', self.clip_slider_unclick)

        self.clip_down_ms = None
        self.clip_up_ms = None
        self.clip_after_id = None
        self.clip_bounds_ms = (None, None)

        self.music_player = MusicPlayer(self.slider, self.slider_lbl, self.update_play_button_text)
        self.music_player.load_song(music_file, song_length_ms)
        self.music_player.reposition(bookmark.position_ms)
        # print(f'VALS: from={from_val}, to={to_val}, val={bookmark.position_ms}')


        # Modal window.
        # Wait for visibility or grab_set doesn't seem to work.
        self.root.wait_visibility()
        self.root.grab_set()
        self.root.transient(parent)


    def clip_slider_click(self, event):
        self.clip_down_ms = self.clip_slider.get()
        self.clip_up_ms = None
        self.cancel_clip_slider_updates()
        self.clip_slider_update()

    def clip_slider_unclick(self, event):
        self.clip_up_ms = self.clip_slider.get()
        self.cancel_clip_slider_updates()
        self.save_clip()
        self.plot()

    def cancel_clip_slider_updates(self):
        print(f'cancelling updates, current = {self.clip_after_id}')
        if self.clip_after_id is not None:
            self.clip_slider.after_cancel(self.clip_after_id)
        self.clip_after_id = None

    def clip_slider_update(self):
        print(f'  UPDATE, clip = {(self.clip_down_ms, self.clip_up_ms)}')
        self.clip_up_ms = self.clip_slider.get()
        self.save_clip()
        self.clip_after_id = self.clip_slider.after(500, self.clip_slider_update)

    def save_clip(self):
        if (self.clip_down_ms is None or
            self.clip_up_ms is None or
            self.clip_up_ms < self.clip_down_ms):
            return
        self.clip_bounds_ms = (self.clip_down_ms, self.clip_up_ms)
        print(f'clip bounds: {self.clip_bounds_ms}')
        self.bookmark.clip_bounds_ms = self.clip_bounds_ms

    def play_pause(self):
        self.music_player.play_pause()

    def update_play_button_text(self, music_player_state):
        txt = 'Play'
        if music_player_state is MusicPlayer.State.PLAYING:
            txt = 'Pause'
        self.play_btn.configure(text = txt)

    def ok(self):
        self.root.grab_release()
        self.bookmark.position_ms = float(self.entry.get())
        self.root.destroy()

    _full_audio_segment = None
    _old_music_file = None

    @classmethod
    def getFullAudioSegment(cls, f):
        # Store the full segment, b/c it takes a while to make.
        if (BookmarkWindow._old_music_file != f or BookmarkWindow._full_audio_segment is None):
            print('loading full segment ...')
            BookmarkWindow._full_audio_segment = AudioSegment.from_mp3(f)
            BookmarkWindow._old_music_file = f
        else:
            print('using cached segment')
        return BookmarkWindow._full_audio_segment
            

    def get_signal_plot_data(self, from_val, to_val):
        sound = BookmarkWindow.getFullAudioSegment(self.music_file)
        sound = sound[from_val : to_val]
        sound = sound.set_channels(1)

        # Hack for plotting: export to a .wav file.  I can't
        # immediately figure out how to directly plot an mp3 (should
        # be possible, as I have all the data), but there are several
        # examples about plotting .wav files,
        # e.g. https://www.geeksforgeeks.org/plotting-various-sounds-on-graphs-using-python-and-matplotlib/
        signal = None
        with NamedTemporaryFile("w+b", suffix=".wav") as f:
            sound.export(f.name, format='wav')
            raw = wave.open(f.name, "r")
            f_rate = raw.getframerate()
            signal = raw.readframes(-1)
            signal = np.frombuffer(signal, dtype = 'int16')

        time = np.linspace(
            0, # start
            len(signal) / f_rate,
            num = len(signal)
        )
        return (time, signal)

    def plot(self):
        fig = Figure(figsize = (5, 1))
        plot1 = fig.add_subplot(111)

        # ref https://stackoverflow.com/questions/2176424/
        #   hiding-axis-text-in-matplotlib-plots
        for x in ['left', 'right', 'top', 'bottom']:
            plot1.spines[x].set_visible(True)
        plot1.set_xticklabels([])
        plot1.set_xticks([])
        plot1.set_yticklabels([])
        plot1.set_yticks([])
        plot1.axes.get_xaxis().set_visible(True)
        plot1.axes.get_yaxis().set_visible(True)

        time, signal = self.signal_plot_data
        plot1.plot(signal)

        # Note we can also do lot1.plot(time, signal), but that
        # doesn't work well with axvspans, as far as I can tell.
        
        # To shade a time span, we have to translate the time into the
        # corresponding index in the signal array.
        def signal_array_index(t_ms):
            span = self.to_val - self.from_val
            pct = (t_ms - self.from_val) / span
            return len(self.signal_plot_data) * pct

        cs, ce = self.bookmark.clip_bounds_ms
        if (cs is not None and ce is not None):
            shade_start = signal_array_index(cs)
            shade_end = signal_array_index(ce)
            self.axv = plot1.axvspan(shade_start, shade_end, alpha=0.25, color='blue')
            # a.remove()

        self.canvas = FigureCanvasTkAgg(fig, master = self.slider_frame)
        self.canvas.get_tk_widget().grid(row=3, column=0, pady=20)

        self.canvas.draw()

        # Can't create Matplotlib toolbar, as it uses pack(), and we're already using grid().
        # toolbar = NavigationToolbar2Tk(canvas, self.root)
        # toolbar.update()
        # canvas.get_tk_widget().grid(row=4, column=0, pady=20)


class MainWindow:

    class Bookmark:
        """A bookmark or clip item, stored in bookmarks listbox"""
        def __init__(self, pos_ms):
            self._pos_ms = pos_ms
            self._clip_start_ms = None
            self._clip_end_ms = None

        def display(self):
            """String description of this for display in list boxes."""
            return f"Bookmark {TimeUtils.time_string(self._pos_ms)}"

        @property
        def position_ms(self):
            """Bookmark position."""
            return self._pos_ms

        @position_ms.setter
        def position_ms(self, v):
            self._pos_ms = v

        @property
        def clip_bounds_ms(self):
            return (self._clip_start_ms, self._clip_end_ms)

        @clip_bounds_ms.setter
        def clip_bounds_ms(self, v):
            self._clip_start_ms, self._clip_end_ms = v

        # TODO remove this.
        def placeholder(self):
            """Demo method, what to do when selected."""
            return f"PLACEHOLDER for {self.display()}"


    class FullTrackBookmark(Bookmark):
        def __init__(self):
            super().__init__(0)
        def display(self):
            return "<Full Track>"


    def __init__(self, window):
        window.title('MP3 Player')
        window.geometry('600x400')
        self.window = window

        self.music_file = None
        self.song_length_ms = 0

        # start_pos_ms is set when the slider is manually
        # repositioned.
        self.start_pos_ms = 0

        self.slider_update_id = None

        # Layout
        master_frame = Frame(window)
        master_frame.pack(pady=20)

        bk_frame = Frame(master_frame)
        bk_frame.grid(row=0, column=0, pady=20)

        # The bookmarks saved during play.
        self.bookmarks = []
        self.bookmarks_lst = Listbox(
            bk_frame,
            width=30,
            selectbackground="yellow",
            selectforeground="black")
        self.bookmarks_lst.grid(row=0, column=1)
        self.bookmarks_lst.bind('<<ListboxSelect>>', self.on_bookmark_select)

        scrollbar = ttk.Scrollbar(bk_frame, orient= 'vertical')
        scrollbar.grid(row=0, column=2, sticky='NS')
        self.bookmarks_lst.config(yscrollcommand= scrollbar.set)
        scrollbar.config(command= self.bookmarks_lst.yview)

        ctl_frame = Frame(master_frame)
        ctl_frame.grid(row=1, column=0, pady=20)

        def _make_button(text, column, command):
            f = ('Times', 10)
            b = Button(ctl_frame, text=text, width=10, font=f, command=command)
            b.grid(row=0, column=column, padx=10)
            return b

        _make_button('Load', 1, self.load)
        self.play_btn = _make_button('Play', 2, self.play_pause)
        self.del_btn =  _make_button('Delete', 3, self.delete_selected_bookmark)
        self.clip_btn = _make_button('Clip', 4, self.popup_window)
        _make_button('Quit', 5, self.quit)

        slider_frame = Frame(master_frame)
        slider_frame.grid(row=2, column=0, pady=20)
        self.slider = ttk.Scale(
            slider_frame,
            from_=0,
            to=100,
            orient=HORIZONTAL,
            value=0,
            length=360)
        self.slider.grid(row=0, column=1, pady=10)

        self.slider_lbl = Label(slider_frame, text='')
        self.slider_lbl.grid(row=1, column=1, pady=2)

        self.music_player = MusicPlayer(self.slider, self.slider_lbl, self.update_play_button_text)
    
        window.bind('<Key>', self.handle_key)

        # during testing
        print("TEST HACK LOAD SONG")
        self._load_song_details('/Users/jeff/Documents/Projects/pytubedl/sample/ten_seconds.mp3')
        self.hack_dev()

    def hack_dev(self):
        self.add_bookmark(3200)
        self.bookmarks_lst.activate(1)
        self.bookmarks_lst.select_set(1)
        self.popup_window()

    def popup_window(self):
        i = self._selected_bookmark_index()
        if not i:
            return
        b = self.bookmarks[i]

        d = BookmarkWindow(self.window, b, self.music_file, self.song_length_ms)
        self.window.wait_window(d.root)
        d.root.grab_release()
        # Re-select, b/c switching to the pop-up deselects the current.
        self.bookmarks_lst.activate(i)
        self.bookmarks_lst.select_set(i)
        self.reload_bookmark_list()
        self.move_to_bookmark(b)

    def reload_bookmark_list(self):
        selected_index = self._selected_bookmark_index()
        self.bookmarks_lst.delete(0, END)
        for b in self.bookmarks:
            self.bookmarks_lst.insert(END, b.display())
        if selected_index:
            self.bookmarks_lst.activate(selected_index)
            self.bookmarks_lst.select_set(selected_index)

    def add_bookmark(self, m):
        b = MainWindow.Bookmark(m)
        self.bookmarks.append(b)
        self.bookmarks_lst.insert(END, b.display())

    def _selected_bookmark_index(self):
        s = self.bookmarks_lst.curselection()
        if len(s) == 0:
            return None
        return int(s[0])

    def update_selected_bookmark(self, new_value_ms):
        i = self._selected_bookmark_index()
        if not i:
            return
        b = self.bookmarks[i]
        if (b.position_ms == new_value_ms):
            return
        b.position_ms = new_value_ms
        self.reload_bookmark_list()

    def delete_selected_bookmark(self):
        index = self._selected_bookmark_index()
        if not index or index == 0:
            return
        del self.bookmarks[index]
        self.reload_bookmark_list()

    def on_bookmark_select(self, event):
        index = self._selected_bookmark_index()
        if not index:
            return
        self.move_to_bookmark(self.bookmarks[index])

    def move_to_bookmark(self, b):
        self.music_player.reposition(b.position_ms)

    def handle_key(self, event):
        k = event.keysym
        if k == 'q':
            self.quit()
        elif k == 'm':
            self.add_bookmark(float(self.slider.get()))
        elif k == 'd':
            self.delete_selected_bookmark()
        elif k == 'p':
            # Previously, I had 'space' handle start/stop, but that
            # also triggers a re-selection of the currently selected
            # bookmark.
            self.play_pause()
        elif k == 'Left':
            self.music_player.increment(-100)
        elif k == 'Right':
            self.music_player.increment(100)
        elif k == 'u':
            self.update_selected_bookmark(float(self.slider.get()))
        # 'plus', 'Return', etc.

    def load(self):
        f = filedialog.askopenfilename()
        if f:
            self._load_song_details(f)
        else:
            print("no file?")

    def _load_song_details(self, f):
        song_mut = MP3(f)
        self.song_length_ms = song_mut.info.length * 1000  # length is in seconds
        self.slider.config(to = self.song_length_ms, value=0)
        self.slider_lbl.configure(text=TimeUtils.time_string(self.song_length_ms))
        self.music_file = f
        self.music_player.load_song(f, self.song_length_ms)
        self.bookmarks = [ MainWindow.FullTrackBookmark() ]
        self.reload_bookmark_list()

    def play_pause(self):
        self.music_player.play_pause()

    def update_play_button_text(self, music_player_state):
        txt = 'Play'
        if music_player_state is MusicPlayer.State.PLAYING:
            txt = 'Pause'
        self.play_btn.configure(text = txt)

    def quit(self):
        self.music_player.stop()
        self.window.destroy()


root = Tk()
mixer.init()
app = MainWindow(root)
root.mainloop()
