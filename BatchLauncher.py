import sys
import traceback
from tkinter import messagebox

from batch_dialog import open_batch_dialog


def main():
    if len(sys.argv) < 2:
        messagebox.showerror(
            "UwUConverter",
            "No folder was supplied."
        )
        return

    open_batch_dialog(sys.argv[1])


if __name__ == "__main__":
    try:
        main()
    except Exception:
        messagebox.showerror(
            "UwUConverter",
            traceback.format_exc()
        )
