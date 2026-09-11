import pathlib
import tkinter as tk
from datetime import datetime
from tkinter import ttk


REPLACE = "replace"
SKIP = "skip"
KEEP_BOTH = "keep_both"
CANCEL = "cancel"


def _format_size(
    size,
):
    size = float(
        size
    )

    for unit in (
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
    ):
        if (
            size < 1024
            or unit == "TB"
        ):
            if unit == "B":
                return (
                    str(int(size))
                    + " B"
                )

            return (
                f"{size:.1f} "
                + unit
            )

        size /= 1024

    return str(
        int(size)
    )


def _file_details(
    path,
):
    path = pathlib.Path(
        path
    )

    if not path.exists():
        return "Does not exist"

    try:
        stat = path.stat()

        modified = datetime.fromtimestamp(
            stat.st_mtime
        ).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        return (
            _format_size(
                stat.st_size
            )
            + "   Modified "
            + modified
        )

    except OSError:
        return "File information unavailable"


def unique_output_path(
    path,
):
    path = pathlib.Path(
        path
    )

    if not path.exists():
        return path

    counter = 1

    while True:
        candidate = path.with_name(
            path.stem
            + " ("
            + str(counter)
            + ")"
            + path.suffix
        )

        if not candidate.exists():
            return candidate

        counter += 1


def show_output_conflict(
    source_path,
    output_path,
    parent=None,
):
    source = pathlib.Path(
        source_path
    )
    output = pathlib.Path(
        output_path
    )

    owns_root = (
        parent is None
    )

    if owns_root:
        window = tk.Tk()
    else:
        window = tk.Toplevel(
            parent
        )
        window.transient(
            parent
        )

    window.title(
        "UwUConverter - File already exists"
    )
    window.resizable(
        False,
        False,
    )

    result = {
        "action": CANCEL,
        "apply_all": False,
    }

    apply_all = tk.BooleanVar(
        value=False
    )

    outer = ttk.Frame(
        window,
        padding=18,
    )
    outer.grid(
        row=0,
        column=0,
        sticky="nsew",
    )

    ttk.Label(
        outer,
        text="A file with this name already exists",
        font=(
            "TkDefaultFont",
            13,
            "bold",
        ),
    ).grid(
        row=0,
        column=0,
        columnspan=3,
        sticky="w",
    )

    ttk.Label(
        outer,
        text=(
            "Choose what UwUConverter should do with the existing output."
        ),
        wraplength=610,
    ).grid(
        row=1,
        column=0,
        columnspan=3,
        sticky="w",
        pady=(
            4,
            14,
        ),
    )

    existing = ttk.LabelFrame(
        outer,
        text="Existing output",
        padding=10,
    )
    existing.grid(
        row=2,
        column=0,
        columnspan=3,
        sticky="ew",
    )

    ttk.Label(
        existing,
        text=str(
            output
        ),
        wraplength=590,
    ).grid(
        row=0,
        column=0,
        sticky="w",
    )

    ttk.Label(
        existing,
        text=_file_details(
            output
        ),
    ).grid(
        row=1,
        column=0,
        sticky="w",
        pady=(
            3,
            0,
        ),
    )

    incoming = ttk.LabelFrame(
        outer,
        text="New conversion",
        padding=10,
    )
    incoming.grid(
        row=3,
        column=0,
        columnspan=3,
        sticky="ew",
        pady=(
            10,
            0,
        ),
    )

    ttk.Label(
        incoming,
        text=str(
            source
        ),
        wraplength=590,
    ).grid(
        row=0,
        column=0,
        sticky="w",
    )

    ttk.Label(
        incoming,
        text=_file_details(
            source
        ),
    ).grid(
        row=1,
        column=0,
        sticky="w",
        pady=(
            3,
            0,
        ),
    )

    keep_path = unique_output_path(
        output
    )

    ttk.Label(
        outer,
        text=(
            "Keep Both will create:\n"
            + str(
                keep_path
            )
        ),
        wraplength=610,
    ).grid(
        row=4,
        column=0,
        columnspan=3,
        sticky="w",
        pady=(
            12,
            0,
        ),
    )

    ttk.Checkbutton(
        outer,
        text="Do this for all remaining conflicts",
        variable=apply_all,
    ).grid(
        row=5,
        column=0,
        columnspan=3,
        sticky="w",
        pady=(
            14,
            12,
        ),
    )

    buttons = ttk.Frame(
        outer
    )
    buttons.grid(
        row=6,
        column=0,
        columnspan=3,
        sticky="e",
    )

    def choose(
        action,
    ):
        result[
            "action"
        ] = action
        result[
            "apply_all"
        ] = bool(
            apply_all.get()
        )
        window.destroy()

    ttk.Button(
        buttons,
        text="Replace",
        command=lambda: choose(
            REPLACE
        ),
    ).grid(
        row=0,
        column=0,
        padx=(
            0,
            6,
        ),
    )

    ttk.Button(
        buttons,
        text="Skip",
        command=lambda: choose(
            SKIP
        ),
    ).grid(
        row=0,
        column=1,
        padx=(
            0,
            6,
        ),
    )

    ttk.Button(
        buttons,
        text="Keep Both",
        command=lambda: choose(
            KEEP_BOTH
        ),
    ).grid(
        row=0,
        column=2,
        padx=(
            0,
            6,
        ),
    )

    ttk.Button(
        buttons,
        text="Cancel",
        command=lambda: choose(
            CANCEL
        ),
    ).grid(
        row=0,
        column=3,
    )

    window.protocol(
        "WM_DELETE_WINDOW",
        lambda: choose(
            CANCEL
        ),
    )

    window.update_idletasks()

    try:
        width = window.winfo_reqwidth()
        height = window.winfo_reqheight()

        screen_width = (
            window.winfo_screenwidth()
        )
        screen_height = (
            window.winfo_screenheight()
        )

        x = max(
            0,
            (
                screen_width
                - width
            )
            // 2,
        )
        y = max(
            0,
            (
                screen_height
                - height
            )
            // 2,
        )

        window.geometry(
            "+"
            + str(x)
            + "+"
            + str(y)
        )
    except tk.TclError:
        pass

    if owns_root:
        window.mainloop()
    else:
        window.grab_set()
        parent.wait_window(
            window
        )

    return result


class ConflictResolver:
    def __init__(
        self,
        parent=None,
    ):
        self.parent = parent
        self.apply_all_action = None

    def resolve(
        self,
        source_path,
        output_path,
    ):
        if self.apply_all_action:
            return self.apply_all_action

        result = show_output_conflict(
            source_path,
            output_path,
            parent=self.parent,
        )

        action = result[
            "action"
        ]

        if (
            result[
                "apply_all"
            ]
            and action != CANCEL
        ):
            self.apply_all_action = (
                action
            )

        return action
