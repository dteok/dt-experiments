from tkinter import *
from tkinter.ttk import *
from time import strftime


def time():
    """Displays time as `string`"""

    string = strftime("%H:%M:%S %p")
    label.config(text=string)  # accesses the attributes of the label widgets created
    label.after(
        1000, time
    )  # displays the time afteer every 1000. 1000 makes a second. It's millisecond


def main():
    """This is the primary function that calls time() and loops
    indefinitely.
    """

    time()
    mainloop()


if __name__ == "__main__":
    root = Tk()
    root.title("Digital Clock")

    label = Label(
        root, font=("ds-digital", 50), background="black", foreground="lightgreen"
    )  # 50 is the font size. change to whatever
    label.pack(anchor="center")  # displays the digital clock in the middle

    main()
