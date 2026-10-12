"""UwUConverter settings window."""
import os
import pathlib
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from version import APP_VERSION

from settings import (
    CATEGORIES,
    CATEGORY_DESCRIPTIONS,
    OPERATION_DEFAULTS,
    get_float,
    load_settings,
    save_settings,
    settings_path,
)


def _open_path(
    path,
):
    path = pathlib.Path(
        path
    )

    if os.name == "nt":
        os.startfile(
            str(path)
        )
        return True

    opener = (
        shutil.which(
            "xdg-open"
        )
        or shutil.which(
            "gio"
        )
    )

    if not opener:
        return False

    if pathlib.Path(
        opener
    ).name == "gio":
        command = [
            opener,
            "open",
            str(path),
        ]
    else:
        command = [
            opener,
            str(path),
        ]

    subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )

    return True


def _browser_extension_folder():
    source_root = pathlib.Path(
        __file__
    ).resolve().parent

    executable_root = pathlib.Path(
        sys.executable
    ).resolve().parent

    candidates = [
        executable_root
        / "browser-extension",
        source_root
        / "browser-extension",
        source_root
        / "browser_extension",
    ]

    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    return candidates[0]


class SettingsWindow:
    def __init__(
        self,
        window,
    ):
        self.window = window
        self.config = (
            load_settings()
        )
        self.dirty = False
        self.loading = True

        self.context_variables = {}
        self.status_var = tk.StringVar(
            value="Settings loaded."
        )

        self.auto_close_var = tk.BooleanVar(
            value=self.config.getboolean(
                "Operations",
                "auto_close_success",
                fallback=True,
            )
        )
        self.auto_close_delay_var = tk.StringVar(
            value=self._format_delay(
                get_float(
                    "Operations",
                    "auto_close_delay",
                    OPERATION_DEFAULTS[
                        "auto_close_delay"
                    ],
                    self.config,
                )
            )
        )
        self.duplicate_var = tk.BooleanVar(
            value=self.config.getboolean(
                "Operations",
                "detect_duplicates",
                fallback=True,
            )
        )
        self.codec_fallback_var = tk.BooleanVar(
            value=self.config.getboolean(
                "Operations",
                "codec_fallback",
                fallback=True,
            )
        )

        self._configure_window()
        self._build_ui()
        self._connect_change_tracking()

        self.loading = False

    def _configure_window(self):
        self.window.title(
            "UwUConverter " + APP_VERSION + " - Settings"
        )
        self.window.geometry(
            "820x650"
        )
        self.window.minsize(
            760,
            590,
        )

        try:
            icon = (
                pathlib.Path(
                    __file__
                ).resolve().parent
                / "UwUConverter.ico"
            )

            if icon.is_file():
                self.window.iconbitmap(
                    str(icon)
                )
        except tk.TclError:
            pass

        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.cancel,
        )

        style = ttk.Style(
            self.window
        )

        try:
            if os.name == "nt":
                style.theme_use(
                    "vista"
                )
        except tk.TclError:
            pass

        style.configure(
            "SettingsHeader.TLabel",
            font=(
                "TkDefaultFont",
                17,
                "bold",
            ),
        )
        style.configure(
            "Section.TLabel",
            font=(
                "TkDefaultFont",
                11,
                "bold",
            ),
        )
        style.configure(
            "Muted.TLabel",
            foreground="#666666",
        )

    @staticmethod
    def _format_delay(
        value,
    ):
        return (
            f"{max(0.0, min(10.0, float(value))):.2f}"
            .rstrip("0")
            .rstrip(".")
        )

    def _build_ui(self):
        outer = ttk.Frame(
            self.window,
            padding=18,
        )
        outer.pack(
            fill="both",
            expand=True,
        )

        header = ttk.Frame(
            outer
        )
        header.pack(
            fill="x",
            pady=(
                0,
                14,
            ),
        )

        title_box = ttk.Frame(
            header
        )
        title_box.pack(
            side="left",
            fill="x",
            expand=True,
        )

        ttk.Label(
            title_box,
            text="UwUConverter Settings",
            style="SettingsHeader.TLabel",
        ).pack(
            anchor="w"
        )

        ttk.Label(
            title_box,
            text=(
                "Control conversions, progress behavior, "
                "right-click menus and integrations."
            ),
            style="Muted.TLabel",
        ).pack(
            anchor="w",
            pady=(
                3,
                0,
            ),
        )

        version_label = ttk.Label(
            header,
            text=APP_VERSION,
            style="Muted.TLabel",
        )
        version_label.pack(
            side="right",
            anchor="n",
            padx=(
                12,
                0,
            ),
        )

        self.notebook = ttk.Notebook(
            outer
        )
        self.notebook.pack(
            fill="both",
            expand=True,
        )

        self.general_tab = ttk.Frame(
            self.notebook,
            padding=18,
        )
        self.context_tab = ttk.Frame(
            self.notebook,
            padding=18,
        )
        self.integrations_tab = ttk.Frame(
            self.notebook,
            padding=18,
        )

        self.notebook.add(
            self.general_tab,
            text="General",
        )
        self.notebook.add(
            self.context_tab,
            text="Context Menu",
        )
        self.notebook.add(
            self.integrations_tab,
            text="Integrations",
        )

        self._build_general_tab()
        self._build_context_tab()
        self._build_integrations_tab()

        ttk.Separator(
            outer
        ).pack(
            fill="x",
            pady=(
                14,
                10,
            ),
        )

        footer = ttk.Frame(
            outer
        )
        footer.pack(
            fill="x",
        )

        ttk.Label(
            footer,
            textvariable=self.status_var,
            style="Muted.TLabel",
        ).pack(
            side="left",
            fill="x",
            expand=True,
        )

        ttk.Button(
            footer,
            text="Cancel",
            command=self.cancel,
        ).pack(
            side="right",
        )

        ttk.Button(
            footer,
            text="Save && Close",
            command=lambda: self.apply(
                close=True
            ),
        ).pack(
            side="right",
            padx=(
                0,
                8,
            ),
        )

        ttk.Button(
            footer,
            text="Apply",
            command=lambda: self.apply(
                close=False
            ),
        ).pack(
            side="right",
            padx=(
                0,
                8,
            ),
        )

    def _build_general_tab(self):
        ttk.Label(
            self.general_tab,
            text="Operations",
            style="Section.TLabel",
        ).pack(
            anchor="w",
        )

        ttk.Label(
            self.general_tab,
            text=(
                "Defaults used by conversion, batch and archive operations."
            ),
            style="Muted.TLabel",
        ).pack(
            anchor="w",
            pady=(
                2,
                12,
            ),
        )

        progress_box = ttk.LabelFrame(
            self.general_tab,
            text="Progress windows",
            padding=14,
        )
        progress_box.pack(
            fill="x",
        )

        ttk.Checkbutton(
            progress_box,
            text=(
                "Automatically close successful progress windows"
            ),
            variable=self.auto_close_var,
        ).grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
        )

        ttk.Label(
            progress_box,
            text=(
                "Failed or cancelled operations always remain open."
            ),
            style="Muted.TLabel",
        ).grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(
                2,
                10,
            ),
        )

        ttk.Label(
            progress_box,
            text="Close after",
        ).grid(
            row=2,
            column=0,
            sticky="w",
        )

        self.delay_spinbox = ttk.Spinbox(
            progress_box,
            from_=0.0,
            to=10.0,
            increment=0.25,
            width=8,
            textvariable=self.auto_close_delay_var,
        )
        self.delay_spinbox.grid(
            row=2,
            column=1,
            sticky="w",
            padx=(
                8,
                5,
            ),
        )

        ttk.Label(
            progress_box,
            text="seconds",
            style="Muted.TLabel",
        ).grid(
            row=2,
            column=2,
            sticky="w",
        )

        behavior_box = ttk.LabelFrame(
            self.general_tab,
            text="Safety and compatibility",
            padding=14,
        )
        behavior_box.pack(
            fill="x",
            pady=(
                14,
                0,
            ),
        )

        ttk.Checkbutton(
            behavior_box,
            text="Detect identical input files",
            variable=self.duplicate_var,
        ).pack(
            anchor="w",
        )

        ttk.Label(
            behavior_box,
            text=(
                "Skips byte-identical duplicates during supported "
                "multi-file and batch operations."
            ),
            style="Muted.TLabel",
            wraplength=700,
        ).pack(
            anchor="w",
            padx=(
                22,
                0,
            ),
            pady=(
                2,
                10,
            ),
        )

        ttk.Checkbutton(
            behavior_box,
            text=(
                "Automatically transcode unsupported media codecs"
            ),
            variable=self.codec_fallback_var,
        ).pack(
            anchor="w",
        )

        ttk.Label(
            behavior_box,
            text=(
                "Recommended. When a video/audio codec cannot be stored "
                "in the selected output container, UwUConverter chooses "
                "an available compatible encoder instead."
            ),
            style="Muted.TLabel",
            wraplength=700,
        ).pack(
            anchor="w",
            padx=(
                22,
                0,
            ),
            pady=(
                2,
                0,
            ),
        )

    def _build_context_tab(self):
        toolbar = ttk.Frame(
            self.context_tab
        )
        toolbar.pack(
            fill="x",
        )

        title_box = ttk.Frame(
            toolbar
        )
        title_box.pack(
            side="left",
            fill="x",
            expand=True,
        )

        ttk.Label(
            title_box,
            text="Right-click menu categories",
            style="Section.TLabel",
        ).pack(
            anchor="w",
        )

        ttk.Label(
            title_box,
            text=(
                "Hide categories you do not use to keep "
                "UwUConverter's menu compact."
            ),
            style="Muted.TLabel",
        ).pack(
            anchor="w",
            pady=(
                2,
                0,
            ),
        )

        button_box = ttk.Frame(
            toolbar
        )
        button_box.pack(
            side="right",
            anchor="n",
        )

        ttk.Button(
            button_box,
            text="All",
            width=7,
            command=lambda: self._set_all_categories(
                True
            ),
        ).pack(
            side="left",
            padx=(
                0,
                4,
            ),
        )

        ttk.Button(
            button_box,
            text="None",
            width=7,
            command=lambda: self._set_all_categories(
                False
            ),
        ).pack(
            side="left",
            padx=(
                0,
                4,
            ),
        )

        ttk.Button(
            button_box,
            text="Defaults",
            command=lambda: self._set_all_categories(
                True
            ),
        ).pack(
            side="left",
        )

        categories = ttk.Frame(
            self.context_tab
        )
        categories.pack(
            fill="both",
            expand=True,
            pady=(
                14,
                0,
            ),
        )

        for row, (
            key,
            title,
        ) in enumerate(
            CATEGORIES.items()
        ):
            variable = tk.BooleanVar(
                value=self.config.getboolean(
                    "ContextMenu",
                    key,
                    fallback=True,
                )
            )
            self.context_variables[
                key
            ] = variable

            item = ttk.Frame(
                categories,
                padding=(
                    0,
                    5,
                ),
            )
            item.grid(
                row=row,
                column=0,
                sticky="ew",
            )
            item.grid_columnconfigure(
                1,
                weight=1,
            )

            ttk.Checkbutton(
                item,
                text=title,
                variable=variable,
            ).grid(
                row=0,
                column=0,
                columnspan=2,
                sticky="w",
            )

            ttk.Label(
                item,
                text=CATEGORY_DESCRIPTIONS[
                    key
                ],
                style="Muted.TLabel",
                wraplength=680,
            ).grid(
                row=1,
                column=1,
                sticky="w",
                padx=(
                    4,
                    0,
                ),
                pady=(
                    1,
                    0,
                ),
            )

        categories.grid_columnconfigure(
            0,
            weight=1,
        )

    def _build_integrations_tab(self):
        ttk.Label(
            self.integrations_tab,
            text="File manager integration",
            style="Section.TLabel",
        ).pack(
            anchor="w",
        )

        if sys.platform == "win32":
            integration_text = (
                "Windows 11's modern menu reads these settings directly. "
                "Windows 10 uses generated registry menus."
            )
        elif sys.platform.startswith(
            "linux"
        ):
            integration_text = (
                "Linux file-manager menus are generated files. "
                "Refresh them after changing context-menu categories."
            )
        else:
            integration_text = (
                "Context-menu integration is not available "
                "on this platform."
            )

        ttk.Label(
            self.integrations_tab,
            text=integration_text,
            style="Muted.TLabel",
            wraplength=700,
        ).pack(
            anchor="w",
            pady=(
                3,
                12,
            ),
        )

        actions = ttk.Frame(
            self.integrations_tab
        )
        actions.pack(
            fill="x",
        )

        ttk.Button(
            actions,
            text="Save && Refresh Context Menus",
            command=self.refresh_context_menus,
        ).pack(
            side="left",
        )

        ttk.Button(
            actions,
            text="Open Browser Extension Folder",
            command=self.open_browser_folder,
        ).pack(
            side="left",
            padx=(
                8,
                0,
            ),
        )

        ttk.Separator(
            self.integrations_tab
        ).pack(
            fill="x",
            pady=18,
        )

        ttk.Label(
            self.integrations_tab,
            text="Settings file",
            style="Section.TLabel",
        ).pack(
            anchor="w",
        )

        setting_path = settings_path()

        path_box = ttk.Frame(
            self.integrations_tab
        )
        path_box.pack(
            fill="x",
            pady=(
                8,
                0,
            ),
        )

        path_var = tk.StringVar(
            value=str(
                setting_path
            )
        )

        ttk.Entry(
            path_box,
            textvariable=path_var,
            state="readonly",
        ).pack(
            side="left",
            fill="x",
            expand=True,
        )

        ttk.Button(
            path_box,
            text="Open Folder",
            command=self.open_settings_folder,
        ).pack(
            side="left",
            padx=(
                8,
                0,
            ),
        )

        ttk.Separator(
            self.integrations_tab
        ).pack(
            fill="x",
            pady=18,
        )

        ttk.Label(
            self.integrations_tab,
            text="Reset",
            style="Section.TLabel",
        ).pack(
            anchor="w",
        )

        ttk.Label(
            self.integrations_tab,
            text=(
                "Restore all operation and context-menu settings "
                "to UwUConverter defaults."
            ),
            style="Muted.TLabel",
        ).pack(
            anchor="w",
            pady=(
                3,
                8,
            ),
        )

        ttk.Button(
            self.integrations_tab,
            text="Restore Defaults",
            command=self.restore_defaults,
        ).pack(
            anchor="w",
        )

    def _connect_change_tracking(self):
        variables = [
            self.auto_close_var,
            self.auto_close_delay_var,
            self.duplicate_var,
            self.codec_fallback_var,
            *self.context_variables.values(),
        ]

        for variable in variables:
            variable.trace_add(
                "write",
                self._mark_dirty,
            )

    def _mark_dirty(
        self,
        *_args,
    ):
        if self.loading:
            return

        self.dirty = True
        self.status_var.set(
            "Unsaved changes."
        )

    def _set_all_categories(
        self,
        value,
    ):
        for variable in (
            self.context_variables.values()
        ):
            variable.set(
                bool(value)
            )

    def _validated_delay(self):
        try:
            value = float(
                self.auto_close_delay_var.get()
            )
        except ValueError:
            raise ValueError(
                "Auto-close delay must be a number."
            )

        if not 0.0 <= value <= 10.0:
            raise ValueError(
                "Auto-close delay must be between 0 and 10 seconds."
            )

        return value

    def _write_to_config(self):
        delay = (
            self._validated_delay()
        )

        if not self.config.has_section(
            "ContextMenu"
        ):
            self.config.add_section(
                "ContextMenu"
            )

        for (
            key,
            variable,
        ) in self.context_variables.items():
            self.config.set(
                "ContextMenu",
                key,
                str(
                    variable.get()
                ).lower(),
            )

        if not self.config.has_section(
            "Operations"
        ):
            self.config.add_section(
                "Operations"
            )

        self.config.set(
            "Operations",
            "auto_close_success",
            str(
                self.auto_close_var.get()
            ).lower(),
        )
        self.config.set(
            "Operations",
            "auto_close_delay",
            self._format_delay(
                delay
            ),
        )
        self.config.set(
            "Operations",
            "detect_duplicates",
            str(
                self.duplicate_var.get()
            ).lower(),
        )
        self.config.set(
            "Operations",
            "codec_fallback",
            str(
                self.codec_fallback_var.get()
            ).lower(),
        )

    def apply(
        self,
        close=False,
    ):
        try:
            self._write_to_config()
            target = (
                save_settings(
                    self.config
                )
            )

        except Exception as error:
            messagebox.showerror(
                "UwUConverter Settings",
                str(error),
                parent=self.window,
            )
            return False

        self.dirty = False
        self.status_var.set(
            "Saved to "
            + str(target)
        )

        if close:
            self.window.destroy()

        return True

    def refresh_context_menus(self):
        if not self.apply(
            close=False
        ):
            return

        try:
            from file_types import file_types

            if sys.platform == "win32":
                import make_key

                make_key.CreateExtensions(
                    file_types
                )

            elif sys.platform.startswith(
                "linux"
            ):
                import linux_menu

                linux_menu.CreateExtensions(
                    file_types
                )

            else:
                raise RuntimeError(
                    "Context-menu integration is not supported on this platform."
                )

            self.status_var.set(
                "Context-menu integration refreshed."
            )

        except Exception as error:
            messagebox.showerror(
                "Refresh Context Menus",
                str(error),
                parent=self.window,
            )

    def open_browser_folder(self):
        folder = (
            _browser_extension_folder()
        )

        if not folder.exists():
            messagebox.showinfo(
                "Browser Extension",
                (
                    "The browser extension folder is not present in this build.\n\n"
                    + str(folder)
                ),
                parent=self.window,
            )
            return

        if not _open_path(
            folder
        ):
            messagebox.showerror(
                "Browser Extension",
                "Could not open the browser extension folder.",
                parent=self.window,
            )

    def open_settings_folder(self):
        folder = (
            settings_path()
            .parent
        )
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not _open_path(
            folder
        ):
            messagebox.showerror(
                "UwUConverter Settings",
                "Could not open the settings folder.",
                parent=self.window,
            )

    def restore_defaults(self):
        if not messagebox.askyesno(
            "Restore defaults?",
            (
                "Restore all settings shown here to their "
                "default values?\n\n"
                "Nothing is saved until you press Apply or Save & Close."
            ),
            parent=self.window,
        ):
            return

        self.loading = True

        try:
            for variable in (
                self.context_variables.values()
            ):
                variable.set(
                    True
                )

            self.auto_close_var.set(
                OPERATION_DEFAULTS[
                    "auto_close_success"
                ]
            )
            self.auto_close_delay_var.set(
                self._format_delay(
                    OPERATION_DEFAULTS[
                        "auto_close_delay"
                    ]
                )
            )
            self.duplicate_var.set(
                OPERATION_DEFAULTS[
                    "detect_duplicates"
                ]
            )
            self.codec_fallback_var.set(
                OPERATION_DEFAULTS[
                    "codec_fallback"
                ]
            )

        finally:
            self.loading = False

        self.dirty = True
        self.status_var.set(
            "Defaults loaded. Press Apply to save them."
        )

    def cancel(self):
        if self.dirty:
            if not messagebox.askyesno(
                "Discard changes?",
                "Close Settings without saving your changes?",
                parent=self.window,
            ):
                return

        self.window.destroy()


def open_settings(
    parent=None,
):
    if parent is None:
        window = tk.Tk()
        SettingsWindow(
            window
        )
        window.mainloop()
        return

    window = tk.Toplevel(
        parent
    )
    window.transient(
        parent
    )

    SettingsWindow(
        window
    )
    parent.wait_window(
        window
    )


if __name__ == "__main__":
    open_settings()
