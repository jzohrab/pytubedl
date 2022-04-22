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
        self.song_length = 0
        self.mixer_init = False
        self.is_playing = False

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
                                command=self.slide,
                                length=360)
        self.slider.grid(row=2, column=0, pady=10)

        # during testing
        print("TEST HACK LOAD SONG")
        self._load_song_details('/Users/jeff/Documents/Projects/pytubedl/sample/ten_seconds.mp3')


    def slide(self, v):
        # This method is called when the user changes the slider,
        # and ALSO from the program loop update_slider().  So,
        # if the user changes the current point, re-load the song.
        current_pos = mixer.music.get_pos()
        f = float(v)
        diff = abs(current_pos - f)
        if diff > 500:
            print(f"suspect user updated, diff = {diff}")
            # mixer.music.set_pos(f / 1000.0)  # can't set_pos
            # mixer.music.load(self.music_file)
            mixer.music.play(loops = 0, start = (f / 1000.0))
            if not self.is_playing:
                mixer.music.pause()
            self.update_slider()
        else:
            print(f"not user updated?, diff = {diff}")

    def update_slider(self):
        if not self.is_playing:
            print("no update needed")
            return

        current_pos = mixer.music.get_pos()
        print(f"current pos = {current_pos} ms")
        print(f"get= {self.slider.get()}")
        # print(f"to= {self.slider.to} ???")
        self.slider.set(current_pos)
        self.slider.after(500, self.update_slider)

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
        self.song_length = song_mut.info.length * 1000  # length is in seconds
        self.slider.config(to = self.song_length, value=0)

    def play(self):
        if self.music_file is None:
            print("no file")
            return

        mixer.init()
        self.mixer_init = True
        mixer.music.load(self.music_file)
        mixer.music.play()
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
