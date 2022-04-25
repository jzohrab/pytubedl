#####
# Clip player
#
# TODO:
# - popup:
"""
- slider with full song, and play and pause, reposition? - reuse existing code
- set start and end of clip
- display start/end of clip in list box (display())
- transcribe
- add note
"""
# - maybe "add note" to bookmark?
# - change bookmark position
# - can't change bookmark pos for <Full Track>"
# - can't add "end clip" for <Full Track>
# - transcribe clip w/ vosk
# - export mp3 file to disk
# - export card and transcription to anki
#
# - any other TODOs in the code.
###


from tkinter import *
from tkinter import filedialog
from pygame import mixer
from mutagen.mp3 import MP3
from enum import Enum
import tkinter.ttk as ttk


class PopupWindow(object):
    """Stub popup window, to be used for bookmark/clip editing."""

    def __init__(self, parent, bookmark):
        # The "return value" of the dialog,
        # entered by user in self.entry Entry box.
        self.bookmark = bookmark

        self.root=Toplevel(parent)
        self.root.protocol('WM_DELETE_WINDOW', self.ok)

        self.entry = Entry(self.root)
        self.entry.insert(END, bookmark.position_ms)
        self.entry.pack()
        self.ok_btn = Button(self.root, text="ok", command=self.ok)
        self.ok_btn.pack()

        # Modal window.
        # Wait for visibility or grab_set doesn't seem to work.
        self.root.wait_visibility()
        self.root.grab_set()
        self.root.transient(parent)

    def ok(self):
        self.root.grab_release()
        self.bookmark.position_ms = float(self.entry.get())
        self.root.destroy()


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

    def __init__(self, slider, slider_lbl):
        self.slider = slider
        self.slider_lbl = slider_lbl

        self.state = MusicPlayer.State.NEW
        self.music_file = None
        self.song_length_ms = 0

        # start_pos_ms is set when the slider is manually
        # repositioned.
        self.start_pos_ms = 0

        self.slider_update_id = None

        self.slider.bind('<Button-1>', self.slider_click)
        self.slider.bind('<ButtonRelease-1>', self.slider_unclick)

    def slider_increment(self, i):
        self.reposition_slider(float(self.slider.get()) + i)

    def slider_click(self, event):
        """User is dragging the slider now, so don't update it."""
        self.cancel_slider_updates()

    def slider_unclick(self, event):
        value_ms_f = float(self.slider.get())
        self.reposition_slider(value_ms_f)

    def reposition_slider(self, value_ms_f):
        v = value_ms_f
        if (v < 0):
            v = 0
        elif (v > self.song_length_ms):
            v = self.song_length_ms

        self.start_pos_ms = v

        self.update_selected_bookmark(v)

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
            if slider_pos < self.song_length_ms:
                old_update_id = self.slider_update_id
                self.slider_update_id = self.slider.after(50, self.update_slider)
            else:
                # Reached the end, stop updating.
                self._pause()

    def load_song(self, f):
        self.stop()
        self.music_file = f
        mixer.music.load(f)

        song_mut = MP3(f)
        self.song_length_ms = song_mut.info.length * 1000  # length is in seconds
        self.slider.config(to = self.song_length_ms, value=0)
        self.start_pos_ms = 0.0

        self.state = MusicPlayer.State.LOADED

    def play_pause(self):
        self.cancel_slider_updates()
        if self.music_file is None:
            return

        if self.state is MusicPlayer.State.LOADED:
            # First play, load and start.
            self.play_btn.configure(text = 'Pause')
            mixer.music.play()
            self.state = MusicPlayer.State.PLAYING
            self.start_pos_ms = 0
            self.update_slider()

        elif self.state is MusicPlayer.State.PLAYING:
            self._pause()

        elif self.state is MusicPlayer.State.PAUSED:
            mixer.music.unpause()
            self.state = MusicPlayer.State.PLAYING
            self.update_slider()
            self.play_btn.configure(text = 'Pause')

        else:
            # Should never get here, but in case I missed something ...
            raise RuntimeError('??? weird state?')

    def _pause(self):
        mixer.music.pause()
        self.cancel_slider_updates()
        self.state = MusicPlayer.State.PAUSED

    def stop(self):
        mixer.music.stop()
        self.cancel_slider_updates()


class MainWindow:

    class State(Enum):
        NEW = 0
        LOADED = 1
        PLAYING = 2
        PAUSED = 3

    class Bookmark:
        """A bookmark or clip item, stored in bookmarks listbox"""
        def __init__(self, pos_ms):
            self._pos_ms = pos_ms

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

        self.state = MainWindow.State.NEW
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

        f = ('Times', 10)
        load_btn = Button(ctl_frame, text='Load', width=10, font=f, command=self.load)
        load_btn.grid(row=0, column=1, padx=10)
        self.play_btn = Button(ctl_frame, text='Play', width=10, font=f, command=self.play_pause)
        self.play_btn.grid(row=0, column=2, padx=10)
        del_btn = Button(ctl_frame, text='Delete', width=10, font=f, command=self.delete_selected_bookmark)
        del_btn.grid(row=0, column=3, padx=10)
        quit_btn = Button(ctl_frame, text='Quit', width=10, font=f, command=self.quit)
        quit_btn.grid(row=0, column=4, padx=10)

        button_bonus = Button(ctl_frame, text="Window", width=10, font=f, command=self.popup_window)
        button_bonus.grid(row=0, column=5, padx=10)

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
        self.slider.bind('<Button-1>', self.slider_click)
        self.slider.bind('<ButtonRelease-1>', self.slider_unclick)

        self.slider_lbl = Label(slider_frame, text='')
        self.slider_lbl.grid(row=1, column=1, pady=2)

        window.bind('<Key>', self.handle_key)

        # during testing
        print("TEST HACK LOAD SONG")
        self._load_song_details('/Users/jeff/Documents/Projects/pytubedl/sample/ten_seconds.mp3')

    def popup_window(self):
        i = self._selected_bookmark_index()
        if not i:
            return
        b = self.bookmarks[i]
        d = PopupWindow(self.window, b)
        print('opened login window, about to wait')
        self.window.wait_window(d.root)
        print('hello back from popping up')
        d.root.grab_release()
        print('reloading after popup')
        # Re-select, b/c switching to the pop-up deselects the current.
        self.bookmarks_lst.activate(i)
        self.bookmarks_lst.select_set(i)
        self.reload_bookmark_list()
        self.move_to_bookmark(b)

    def reload_bookmark_list(self):
        selected_index = self._selected_bookmark_index()
        print(f'reloading with sel ind = {selected_index}')
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
        print (f'bookmark selected: {(b.placeholder())}')
        self.reposition_slider(b.position_ms)

    def handle_key(self, event):
        k = event.keysym
        print(f'got key: {k}')
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
            self.slider_increment(-100)
        elif k == 'Right':
            self.slider_increment(100)
        elif k == 'u':
            self.update_selected_bookmark(float(self.slider.get()))
        # 'plus', 'Return', etc.

    def slider_increment(self, i):
        self.reposition_slider(float(self.slider.get()) + i)

    def slider_click(self, event):
        """User is dragging the slider now, so don't update it."""
        self.cancel_slider_updates()

    def slider_unclick(self, event):
        value_ms_f = float(self.slider.get())
        self.reposition_slider(value_ms_f)

    def reposition_slider(self, value_ms_f):
        v = value_ms_f
        if (v < 0):
            v = 0
        elif (v > self.song_length_ms):
            v = self.song_length_ms

        self.start_pos_ms = v

        self.update_selected_bookmark(v)

        mixer.music.play(loops = 0, start = (v / 1000.0))
        if self.state is not MainWindow.State.PLAYING:
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

        if self.state is MainWindow.State.PLAYING:
            if slider_pos < self.song_length_ms:
                old_update_id = self.slider_update_id
                self.slider_update_id = self.slider.after(50, self.update_slider)
            else:
                # Reached the end, stop updating.
                self._pause()


    def load(self):
        f = filedialog.askopenfilename()
        if f:
            self._load_song_details(f)
        else:
            print("no file?")

    def _load_song_details(self, f):
        self.stop()
        self.music_file = f
        mixer.music.load(f)

        song_mut = MP3(f)
        self.song_length_ms = song_mut.info.length * 1000  # length is in seconds
        self.slider.config(to = self.song_length_ms, value=0)
        self.start_pos_ms = 0.0

        self.bookmarks = [ MainWindow.FullTrackBookmark() ]
        self.reload_bookmark_list()
        self.state = MainWindow.State.LOADED

    def play_pause(self):
        self.cancel_slider_updates()
        if self.music_file is None:
            return

        if self.state is MainWindow.State.LOADED:
            # First play, load and start.
            self.play_btn.configure(text = 'Pause')
            mixer.music.play()
            self.state = MainWindow.State.PLAYING
            self.start_pos_ms = 0
            self.update_slider()

        elif self.state is MainWindow.State.PLAYING:
            self._pause()

        elif self.state is MainWindow.State.PAUSED:
            mixer.music.unpause()
            self.state = MainWindow.State.PLAYING
            self.update_slider()
            self.play_btn.configure(text = 'Pause')

        else:
            # Should never get here, but in case I missed something ...
            raise RuntimeError('??? weird state?')

    def _pause(self):
        mixer.music.pause()
        self.cancel_slider_updates()
        self.state = MainWindow.State.PAUSED
        self.play_btn.configure(text = 'Play')

    def stop(self):
        mixer.music.stop()
        self.cancel_slider_updates()

    def quit(self):
        mixer.music.stop()
        self.window.destroy()


root = Tk()
mixer.init()
app = MainWindow(root)
root.mainloop()
