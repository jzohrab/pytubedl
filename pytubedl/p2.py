from tkinter import *
from tkinter import filedialog
from pygame import mixer

class MusicPlayer:
    def __init__(self, window ):
        window.geometry('320x100'); window.title('Iris Player'); window.resizable(0,0)
        f = ('Times', 10)

        play_img = PhotoImage(file='./images/play50.png')
        Load = Button(window, text='Load', width=10, font=f, command=self.load)
        Play = Button(window, text='Play', width=10, font=f, command=self.play)
        Pause = Button(window, text='Pause', width=10, font=f, command=self.pause)
        Stop = Button(window ,text='Stop', width=10, font=f, command=self.stop)

        Load.place(x=0,y=20)
        Play.place(x=110,y=20)
        Pause.place(x=220,y=20)
        Stop.place(x=110,y=60)

        self.music_file = None
        self.mixer_init = False
        self.playing_state = False

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
