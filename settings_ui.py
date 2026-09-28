"""Compact context-menu and operations preferences."""
import tkinter as tk
from tkinter import ttk, messagebox
from settings import CATEGORIES, load_settings, save_settings


def open_settings():
    root = tk.Tk()
    root.title("UwUConverter 3.2 - Settings")
    root.resizable(False, False)
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Context-menu customization", font=("TkDefaultFont", 15, "bold")).pack(anchor="w")
    ttk.Label(frame, text="Choose which UwUConverter actions appear when you right-click.").pack(anchor="w", pady=(3, 14))
    config = load_settings()
    variables = {}
    for key, title in CATEGORIES.items():
        var = tk.BooleanVar(value=config.getboolean("ContextMenu", key, fallback=True))
        variables[key] = var
        ttk.Checkbutton(frame, text=title, variable=var).pack(anchor="w", pady=3)
    ttk.Separator(frame).pack(fill="x", pady=12)
    ttk.Label(frame, text="Operations", font=("TkDefaultFont", 12, "bold")).pack(anchor="w")
    autoquit = tk.BooleanVar(value=config.getboolean("Operations", "auto_close_success", fallback=True))
    detect = tk.BooleanVar(value=config.getboolean("Operations", "detect_duplicates", fallback=True))
    ttk.Checkbutton(frame, text="Automatically close progress window after successful completion", variable=autoquit).pack(anchor="w", pady=4)
    ttk.Checkbutton(frame, text="Detect and skip identical input files", variable=detect).pack(anchor="w", pady=4)
    ttk.Label(frame, text="Windows 11 menu changes appear when Explorer next refreshes.\nWindows 10/Linux: run integration setup after saving.").pack(anchor="w", pady=12)
    def save():
        if not config.has_section("ContextMenu"):
            config.add_section("ContextMenu")
        for key, variable in variables.items():
            config.set("ContextMenu", key, str(variable.get()).lower())
        if not config.has_section("Operations"):
            config.add_section("Operations")
        config.set("Operations", "auto_close_success", str(autoquit.get()).lower())
        config.set("Operations", "detect_duplicates", str(detect.get()).lower())
        save_settings(config)
        root.destroy()
    ttk.Button(frame, text="Save settings", command=save).pack(anchor="e")
    root.mainloop()

if __name__ == "__main__":
    open_settings()
