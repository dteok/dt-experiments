from tkinter import Tk
from tkinter import mainloop
import TextLable

class ClockWindow:
    _window = None
    _lable = None

    def __init__(self, Title, Geometry):
        self._window = Tk()
        self._window.title(Title)
        self._window.geometry(Geometry)
        self._window.resizable(0, 0)

        self._lable = TextLable.TextLable(self._window)
        self._lable.update()


if __name__ == "__main__":
    ClockWindow("Digital Clock", "370x100")
    mainloop()
