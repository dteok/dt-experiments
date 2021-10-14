from tkinter import *
from tkinter.ttk import *
from time import strftime


# TODO:
# To display day of the week -- Saturday
# To display date   -- 23 September 2021


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
    root.geometry("370x100")
    root.resizable(0, 0)

    label = Label(
        root,
        font=("ds-digital", 50, "bold"),
        background="black",
        foreground="lightgreen",
        borderwidth=25,
        border=25,
    )  # 50 is the font size. change to whatever
    label.pack(anchor="center")  # displays the digital clock in the middle
    # label.grid(row=2, column=2, pady=5, padx=10)
    label.pack(
        anchor="center", fill="both", expand=1
    )  # resolves expanding/shrinking when second ticks to 01 (narrowest)

    main()
