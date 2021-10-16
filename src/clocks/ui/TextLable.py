from tkinter import Label
from tkinter import Tk
from tkinter import mainloop
from time import strftime

class TextLable:

    label = None

    def __init__(self, parent):
        self.label = Label(
            parent,
            font=("ds-digital", 50, "bold"),
            background="black",
            foreground="lightgreen",
            borderwidth=25,
            border=25,
        )  # 50 is the font size. change to whatever
        self.label.pack(anchor="center")  # displays the digital clock in the middle
        # label.grid(row=2, column=2, pady=5, padx=10)
        self.label.pack(
            anchor="center", fill="both", expand=1
        )  # resolves expanding/shrinking when second ticks to 01 (narrowest)

    def update(self):
        string = strftime("%H:%M:%S %p")
        self.label.config(text=string)  # accesses the attributes of the label widgets created
        self.label.after(
            1000, self.update
        )  # displays the time afteer every 1000. 1000 makes a second. It's millisecond

if __name__ == "__main__":
    appwindow = Tk()
    appwindow.title("Digital Clock")
    appwindow.geometry("370x100")
    appwindow.resizable(0, 0)

    label = TextLable(appwindow)
    label.update()
    mainloop()
