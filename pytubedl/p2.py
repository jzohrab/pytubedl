from tkinter import *
from tkinter import filedialog
from pygame import mixer
from mutagen.mp3 import MP3

import tkinter.ttk as ttk

class MusicPlayer:

    def __init__(self, window):
        window.title('MP3 Player')
        window.geometry('500x400')

        self.music_file = None
        self.song_length_ms = 0
        self.mixer_init = False
        self.is_playing = False
        self.start_pos_ms = 0

        self.user_changing_slider = False
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

        controls_frame = Frame(master_frame)
        controls_frame.grid(row=1, column=0, pady=20)

        f = ('Times', 10)
        load_button = Button(controls_frame, text='Load', width=10, font=f, command=self.load)
        play_button = Button(controls_frame, text='Play', width=10, font=f, command=self.play)
        pause_button = Button(controls_frame, text='Pause', width=10, font=f, command=self.pause)
        stop_button = Button(controls_frame ,text='Stop', width=10, font=f, command=self.stop)

        load_button.grid(row=0, column=1, padx=10)
        play_button.grid(row=0, column=2, padx=10)
        pause_button.grid(row=0, column=3, padx=10)
        stop_button.grid(row=0, column=4, padx=10)

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
        print("sl click")
        self.user_changing_slider = True
        if self.slider_update_id:
            self.slider.after_cancel(self.slider_update_id)
        print(self.slider.get())

    def slider_unclick(self, event):
        self.user_changing_slider = False
        value_ms_f = float(self.slider.get())
        print(f"sl UNclick, reloading at current point {value_ms_f}")
        mixer.music.play(loops = 0, start = (value_ms_f / 1000.0))
        self.start_pos_ms = value_ms_f
        if not self.is_playing:
            mixer.music.pause()
        self.update_slider()

    def update_slider(self):
        print('entered update_slider')
        if not self.mixer_init:
            return

        if not self.is_playing:
            print("no update needed")
            return

        current_pos_ms = mixer.music.get_pos()
        print(f"current pos = {current_pos_ms} ms")
        print(f"get= {self.slider.get()}")
        # print(f"to= {self.slider.to} ???")
        self.slider.set(self.start_pos_ms + current_pos_ms)
        self.slider_update_id = self.slider.after(500, self.update_slider)

    def load(self):
        f = filedialog.askopenfilename()
        if f:
            self._load_song_details(f)
        else:
            print("no file?")

    def _load_song_details(self, f):
        self.is_playing = False
        print(f"Got file {f}")
        self.music_file = f
        song_mut = MP3(f)
        self.song_length_ms = song_mut.info.length * 1000  # length is in seconds
        self.slider.config(to = self.song_length_ms, value=0)
        self.start_pos_ms = 0.0

    def play(self):
        if self.music_file is None:
            print("no file")
            return

        mixer.init()
        self.mixer_init = True
        mixer.music.load(self.music_file)
        mixer.music.play()
        self.start_pos_ms = 0
        self.is_playing = True
        print("set is_playing to True just now")
        self.update_slider()

    def pause(self):
        if not self.mixer_init:
            return
        if self.is_playing:
            mixer.music.pause()
            self.is_playing = False
        else:
            mixer.music.unpause()
            self.is_playing = True
            self.update_slider()

    def stop(self):
        if not self.mixer_init:
            return
        mixer.music.stop()
        self.is_playing = False

root = Tk()
app= MusicPlayer(root)
root.mainloop()
