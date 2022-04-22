from tkinter import *
from tkinter import filedialog
from pygame import mixer
from mutagen.mp3 import MP3
from enum import Enum
import tkinter.ttk as ttk

class MusicPlayer:

    class State(Enum):
        NEW = 0
        LOADED = 1
        PLAYING = 2
        PAUSED = 3

    def __init__(self, window):
        window.title('MP3 Player')
        window.geometry('600x400')

        mixer.init()

        self.state = MusicPlayer.State.NEW
        self.music_file = None
        self.song_length_ms = 0
        self.start_pos_ms = 0

        self.slider_update_id = None

        # Layout
        master_frame = Frame(window)
        master_frame.pack(pady=20)

        song_box = Listbox(master_frame,
                           bg="black", fg="green",
                           width=60,
                           selectbackground="green",
                           selectforeground="black")
        song_box.grid(row=0, column=0)

        ctl_frame = Frame(master_frame)
        ctl_frame.grid(row=1, column=0, pady=20)

        f = ('Times', 10)
        load_btn = Button(ctl_frame, text='Load', width=10, font=f, command=self.load)
        load_btn.grid(row=0, column=1, padx=10)
        self.play_btn = Button(ctl_frame, text='Play', width=10, font=f, command=self.play_pause)
        self.play_btn.grid(row=0, column=2, padx=10)

        self.slider = ttk.Scale(master_frame,
                                from_=0,
                                to=100,
                                orient=HORIZONTAL,
                                value=0,
                                length=360)
        self.slider.grid(row=2, column=0, pady=10)
        self.slider.bind('<Button-1>', self.slider_click)
        self.slider.bind('<ButtonRelease-1>', self.slider_unclick)

        # during testing
        print("TEST HACK LOAD SONG")
        self._load_song_details('/Users/jeff/Documents/Projects/pytubedl/sample/ten_seconds.mp3')


    def slider_click(self, event):
        self.cancel_slider_updates()

    def slider_unclick(self, event):
        value_ms_f = float(self.slider.get())
        mixer.music.play(loops = 0, start = (value_ms_f / 1000.0))
        self.start_pos_ms = value_ms_f
        if self.state is MusicPlayer.State.PAUSED:
            mixer.music.pause()
        self.update_slider()

    def cancel_slider_updates(self):
        if self.slider_update_id:
            self.slider.after_cancel(self.slider_update_id)

    def update_slider(self):
        if self.state is not MusicPlayer.State.PLAYING:
            return
        current_pos_ms = mixer.music.get_pos()
        slider_pos = self.start_pos_ms + current_pos_ms
        self.slider.set(slider_pos)
        if slider_pos < self.song_length_ms:
            self.slider_update_id = self.slider.after(50, self.update_slider)
        else:
            self.cancel_slider_updates()
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
            mixer.music.load(self.music_file)
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
        self.play_btn.configure(text = 'Play')

    def stop(self):
        mixer.music.stop()
        self.cancel_slider_updates()

root = Tk()
app= MusicPlayer(root)
root.mainloop()
