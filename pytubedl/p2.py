from tkinter import *
from tkinter import filedialog
from pygame import mixer

import tkinter.ttk as ttk

class MusicPlayer:
    def __init__(self, window):
        window.title('MP3 Player')
        window.geometry('500x400')
        # window.resizable(0,0)

        f = ('Times', 10)
        play_img = PhotoImage(file='./images/play50.png')

        self.music_file = None
        self.mixer_init = False
        self.playing_state = False

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

        load_button = Button(controls_frame, text='Load', width=10, font=f, command=self.load)
        play_button = Button(controls_frame, text='Play', width=10, font=f, command=self.play)
        pause_button = Button(controls_frame, text='Pause', width=10, font=f, command=self.pause)
        stop_button = Button(controls_frame ,text='Stop', width=10, font=f, command=self.stop)

        load_button.grid(row=0, column=1, padx=10)
        play_button.grid(row=0, column=2, padx=10)
        pause_button.grid(row=0, column=3, padx=10)
        stop_button.grid(row=0, column=4, padx=10)

        my_slider = ttk.Scale(master_frame,
                              from_=0,
                              to=100,
                              orient=HORIZONTAL,
                              value=0,
                              command=self.slide,
                              length=360)
        my_slider.grid(row=2, column=0, pady=10)


    def slide(self, v):
        print(f"todo, slider position = {v}")

    def load(self):
        self.music_file = filedialog.askopenfilename()

    def play(self):
        if self.music_file is None:
            print("no file")

        mixer.init()
        self.mixer_init = True
        mixer.music.load(self.music_file)
        mixer.music.play()

    def pause(self):
        if not self.mixer_init:
            return
        if not self.playing_state:
            mixer.music.pause()
            self.playing_state=True
        else:
            mixer.music.unpause()
            self.playing_state = False

    def stop(self):
        if not self.mixer_init:
            return
        mixer.music.stop()

root = Tk()
app= MusicPlayer(root)
root.mainloop()
