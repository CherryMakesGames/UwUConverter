import queue
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from batch_converter import batch_convert_folder


FORMATS = {
    "image": ["PNG", "JPG", "JPEG", "WEBP", "ICO", "TIF", "TIFF", "PDF"],
    "video": [
        "MP4", "MKV", "MOV", "AVI", "WEBM",
        "MP3", "WAV", "FLAC", "OGG", "OPUS"
    ],
    "audio": ["MP3", "WAV", "FLAC", "OGG", "OPUS"],
    "document": ["PDF", "DOCX", "ODT", "TXT"],
    "spreadsheet": [
        "PDF", "XLSX", "XLS", "ODS", "CSV", "TSV"
    ],
    "model": ["OBJ", "STL", "PLY", "GLB"],
}

CATEGORY_LABELS = {
    "image": "Images",
    "video": "Video",
    "audio": "Audio",
    "document": "Documents",
    "spreadsheet": "Spreadsheets",
    "model": "3D Models",
}

MODE_LABELS = {
    "replace": "Replace originals",
    "folder": "Create a new folder beside the original folder",
    "beside": "Place converted files beside originals",
}


def open_batch_dialog(folder_path, category=None):
    root = tk.Tk()
    root.title("UwUConverter - Batch Converter")
    root.resizable(False, False)

    events = queue.Queue()
    cancel_event = threading.Event()
    worker = None

    frame = ttk.Frame(root, padding=18)
    frame.grid(row=0, column=0)

    ttk.Label(
        frame,
        text="UwUConverter Batch Converter",
        font=("", 13, "bold")
    ).grid(
        row=0,
        column=0,
        columnspan=2,
        sticky="w",
        pady=(0, 12)
    )

    ttk.Label(
        frame,
        text="Folder:"
    ).grid(
        row=1,
        column=0,
        sticky="nw",
        padx=(0, 10)
    )

    ttk.Label(
        frame,
        text=folder_path,
        wraplength=460
    ).grid(
        row=1,
        column=1,
        sticky="w"
    )

    ttk.Label(
        frame,
        text="Category:"
    ).grid(
        row=2,
        column=0,
        sticky="w",
        padx=(0, 10),
        pady=(14, 4)
    )

    category_box = ttk.Combobox(
        frame,
        state="readonly",
        width=24,
        values=list(CATEGORY_LABELS.values())
    )
    category_box.grid(
        row=2,
        column=1,
        sticky="w",
        pady=(14, 4)
    )

    ttk.Label(
        frame,
        text="Output mode:"
    ).grid(
        row=3,
        column=0,
        sticky="w",
        padx=(0, 10),
        pady=4
    )

    mode_box = ttk.Combobox(
        frame,
        state="readonly",
        width=46,
        values=list(MODE_LABELS.values())
    )
    mode_box.current(1)
    mode_box.grid(
        row=3,
        column=1,
        sticky="w",
        pady=4
    )

    ttk.Label(
        frame,
        text="Format:"
    ).grid(
        row=4,
        column=0,
        sticky="w",
        padx=(0, 10),
        pady=4
    )

    format_box = ttk.Combobox(
        frame,
        state="readonly",
        width=18
    )
    format_box.grid(
        row=4,
        column=1,
        sticky="w",
        pady=4
    )

    create_log_value = tk.BooleanVar(
        value=False
    )

    create_log_checkbox = ttk.Checkbutton(
        frame,
        text="Create log file in the source folder",
        variable=create_log_value
    )
    create_log_checkbox.grid(
        row=10,
        column=0,
        columnspan=2,
        sticky="w",
        pady=(8, 0)
    )

    def selected_category():
        selected_label = category_box.get()

        return next(
            key
            for key, label in CATEGORY_LABELS.items()
            if label == selected_label
        )

    def refresh_formats(event=None):
        selected = selected_category()
        format_box["values"] = FORMATS[selected]
        format_box.current(0)

    default_category = (
        category
        if category in FORMATS
        else "image"
    )

    category_box.set(
        CATEGORY_LABELS[default_category]
    )
    refresh_formats()

    category_box.bind(
        "<<ComboboxSelected>>",
        refresh_formats
    )

    progress = ttk.Progressbar(
        frame,
        orient="horizontal",
        length=470,
        mode="determinate",
        maximum=1
    )
    progress.grid(
        row=5,
        column=0,
        columnspan=2,
        sticky="ew",
        pady=(18, 6)
    )

    status = ttk.Label(
        frame,
        text="Ready."
    )
    status.grid(
        row=6,
        column=0,
        columnspan=2,
        sticky="w"
    )

    counters = ttk.Label(
        frame,
        text=""
    )
    counters.grid(
        row=7,
        column=0,
        columnspan=2,
        sticky="w",
        pady=(3, 0)
    )

    current_file = ttk.Label(
        frame,
        text="",
        wraplength=470
    )
    current_file.grid(
        row=8,
        column=0,
        columnspan=2,
        sticky="w",
        pady=(3, 0)
    )

    buttons = ttk.Frame(frame)
    buttons.grid(
        row=9,
        column=0,
        columnspan=2,
        sticky="e",
        pady=(18, 0)
    )

    def set_controls(enabled):
        state = "readonly" if enabled else "disabled"
        category_box.config(state=state)
        mode_box.config(state=state)
        format_box.config(state=state)
        create_log_checkbox.config(
            state="normal" if enabled else "disabled"
        )
        start_button.config(
            state="normal" if enabled else "disabled"
        )

    def progress_callback(data):
        events.put(("progress", data))

    def worker_main(action, create_log):
        try:
            stats = batch_convert_folder(
                folder_path,
                action,
                progress_callback=progress_callback,
                cancel_event=cancel_event,
                create_log=create_log
            )
            events.put(("finished", stats))
        except Exception as error:
            events.put(("error", error))

    def start_conversion():
        nonlocal worker

        selected = selected_category()
        selected_mode_label = mode_box.get()

        selected_mode = next(
            key
            for key, label in MODE_LABELS.items()
            if label == selected_mode_label
        )

        selected_format = format_box.get().lower()

        if selected_mode == "replace":
            confirmed = messagebox.askyesno(
                "Replace originals?",
                "Successfully converted files will replace "
                "their originals. Failed files will be kept.\n\n"
                "Continue?"
            )

            if not confirmed:
                return

        action = (
            "batch_"
            + selected
            + "_"
            + selected_mode
            + "_"
            + selected_format
        )

        cancel_event.clear()
        set_controls(False)
        cancel_button.config(state="normal")
        progress.config(mode="indeterminate")
        progress.start(12)
        status.config(text="Scanning folder...")
        counters.config(text="")
        current_file.config(text="")

        worker = threading.Thread(
            target=worker_main,
            args=(
                action,
                create_log_value.get()
            ),
            daemon=True
        )
        worker.start()

    def request_cancel():
        if worker is None or not worker.is_alive():
            root.destroy()
            return

        cancel_event.set()
        cancel_button.config(state="disabled")
        status.config(
            text="Cancelling after the current file..."
        )

    def handle_progress(data):
        phase = data["phase"]

        if phase == "counting":
            status.config(
                text=(
                    "Scanning folder... "
                    f"{data['scanned']:,} entries checked"
                )
            )
            return

        if phase == "converting":
            if str(progress["mode"]) != "determinate":
                progress.stop()
                progress.config(mode="determinate")

            total = max(data["matched"], 1)
            progress.config(maximum=total)
            progress["value"] = data["processed"]

            status.config(
                text=(
                    f"Converting {data['processed']:,} "
                    f"of {data['matched']:,}"
                )
            )

            counters.config(
                text=(
                    f"Converted: {data['converted']:,}    "
                    f"Skipped: {data['skipped']:,}    "
                    f"Failed: {data['failed']:,}"
                )
            )

            current_file.config(
                text=(
                    "Current file: "
                    + data["current_file"]
                    if data["current_file"]
                    else ""
                )
            )

    def poll_events():
        try:
            while True:
                event_type, payload = events.get_nowait()

                if event_type == "progress":
                    handle_progress(payload)

                elif event_type == "finished":
                    progress.stop()
                    progress.config(mode="determinate")
                    progress["value"] = progress["maximum"]
                    set_controls(True)
                    cancel_button.config(
                        state="normal"
                    )

                    if payload["cancelled"]:
                        status.config(text="Batch cancelled.")
                        messagebox.showinfo(
                            "Batch cancelled",
                            "Processed: "
                            + f"{payload['processed']:,}"
                            + "\nConverted: "
                            + f"{payload['converted']:,}"
                            + "\nFailed: "
                            + f"{payload['failed']:,}"
                            + (
                                "\n\nLog:\n"
                                + payload["log_path"]
                                if payload["log_path"]
                                else ""
                            )
                        )
                    else:
                        status.config(text="Batch complete.")
                        messagebox.showinfo(
                            "Batch complete",
                            "Converted: "
                            + f"{payload['converted']:,}"
                            + "\nSkipped: "
                            + f"{payload['skipped']:,}"
                            + "\nFailed: "
                            + f"{payload['failed']:,}"
                            + (
                                "\n\nLog:\n"
                                + payload["log_path"]
                                if payload["log_path"]
                                else ""
                            )
                        )

                elif event_type == "error":
                    progress.stop()
                    set_controls(True)
                    cancel_button.config(
                        state="normal"
                    )
                    status.config(text="Conversion failed.")
                    messagebox.showerror(
                        "Batch conversion failed",
                        str(payload)
                    )

        except queue.Empty:
            pass

        root.after(50, poll_events)

    start_button = ttk.Button(
        buttons,
        text="Start conversion",
        command=start_conversion
    )
    start_button.grid(
        row=0,
        column=1
    )

    cancel_button = ttk.Button(
        buttons,
        text="Close",
        command=request_cancel
    )
    cancel_button.grid(
        row=0,
        column=0,
        padx=(0, 8)
    )

    root.protocol(
        "WM_DELETE_WINDOW",
        request_cancel
    )

    root.after(50, poll_events)
    root.mainloop()
