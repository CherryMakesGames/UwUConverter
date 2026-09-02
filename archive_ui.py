import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk

from archive_manager import (
    add_to_archive,
    create_archive,
    delete_archive_entries,
    extract_archive_entries,
    list_archive_entries,
    test_archive,
)


ARCHIVE_FILE_TYPES = [
    (
        "Archives",
        (
            "*.7z *.zip *.rar *.tar *.gz *.gzip "
            "*.bz2 *.bzip2 *.xz *.wim *.cab *.iso "
            "*.arj *.lzh *.lzma *.rpm *.dmg *.xar"
        ),
    ),
    ("All files", "*.*"),
]


def _format_size(value):
    value = int(
        value or 0
    )

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
    ]

    size = float(value)

    for unit in units:
        if (
            size < 1024
            or unit == units[-1]
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

    return str(value)


def _open_path(path):
    path = str(path)

    if os.name == "nt":
        os.startfile(
            path
        )
        return

    opener = (
        shutil.which(
            "xdg-open"
        )
        or shutil.which(
            "gio"
        )
    )

    if not opener:
        return

    if pathlib.Path(
        opener
    ).name == "gio":
        command = [
            opener,
            "open",
            path,
        ]
    else:
        command = [
            opener,
            path,
        ]

    subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )


class ArchiveManagerWindow:
    def __init__(
        self,
        root,
        archive_path=None,
    ):
        self.root = root
        self.archive_path = None
        self.entries = []
        self.current_folder = ""
        self.password = None
        self.item_map = {}

        self.path_var = tk.StringVar(
            value="No archive open"
        )
        self.folder_var = tk.StringVar(
            value="/"
        )
        self.status_var = tk.StringVar(
            value="Ready"
        )

        self.root.title(
            "UwUConverter Archive Manager"
        )
        self.root.geometry(
            "940x610"
        )
        self.root.minsize(
            720,
            430,
        )

        self._set_window_icon()
        self._build_menu()
        self._build_toolbar()
        self._build_address_bar()
        self._build_file_list()
        self._build_status_bar()

        if archive_path:
            self.open_archive(
                archive_path
            )

    def _set_window_icon(self):
        candidates = [
            pathlib.Path(
                __file__
            ).resolve().parent
            / "UwUConverter.ico",
            pathlib.Path(
                sys.executable
            ).resolve().parent
            / "UwUConverter.ico",
        ]

        for candidate in candidates:
            if not candidate.is_file():
                continue

            try:
                self.root.iconbitmap(
                    str(candidate)
                )
                break
            except tk.TclError:
                pass

    def _build_menu(self):
        menu = tk.Menu(
            self.root
        )

        file_menu = tk.Menu(
            menu,
            tearoff=False,
        )
        file_menu.add_command(
            label="Open archive...",
            command=self.choose_archive,
        )
        file_menu.add_command(
            label="New archive...",
            command=self.new_archive,
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Close archive",
            command=self.close_archive,
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit",
            command=self.root.destroy,
        )
        menu.add_cascade(
            label="File",
            menu=file_menu,
        )

        commands = tk.Menu(
            menu,
            tearoff=False,
        )
        commands.add_command(
            label="Add files...",
            command=self.add_files,
        )
        commands.add_command(
            label="Add folder...",
            command=self.add_folder,
        )
        commands.add_command(
            label="Extract to...",
            command=self.extract_selected,
        )
        commands.add_command(
            label="Test archive",
            command=self.test_current_archive,
        )
        commands.add_command(
            label="Delete selected",
            command=self.delete_selected,
        )
        menu.add_cascade(
            label="Commands",
            menu=commands,
        )

        tools = tk.Menu(
            menu,
            tearoff=False,
        )
        tools.add_command(
            label="Set extraction password...",
            command=self.set_password,
        )
        tools.add_command(
            label="Clear password",
            command=self.clear_password,
        )
        tools.add_separator()
        tools.add_command(
            label="Refresh",
            command=self.refresh,
        )
        menu.add_cascade(
            label="Tools",
            menu=tools,
        )

        help_menu = tk.Menu(
            menu,
            tearoff=False,
        )
        help_menu.add_command(
            label="Archive information",
            command=self.show_info,
        )
        help_menu.add_command(
            label="About",
            command=self.show_about,
        )
        menu.add_cascade(
            label="Help",
            menu=help_menu,
        )

        self.root.configure(
            menu=menu
        )

    def _toolbar_button(
        self,
        parent,
        text,
        command,
    ):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            width=11,
            height=2,
            relief="raised",
            bd=1,
            padx=4,
            pady=2,
        )
        button.pack(
            side="left",
            padx=(
                0,
                5,
            ),
        )
        return button

    def _build_toolbar(self):
        frame = tk.Frame(
            self.root,
            bd=1,
            relief="raised",
            padx=6,
            pady=6,
        )
        frame.pack(
            fill="x",
        )

        self._toolbar_button(
            frame,
            "Add",
            self.add_files,
        )
        self._toolbar_button(
            frame,
            "Extract To",
            self.extract_selected,
        )
        self._toolbar_button(
            frame,
            "Test",
            self.test_current_archive,
        )
        self._toolbar_button(
            frame,
            "Delete",
            self.delete_selected,
        )
        self._toolbar_button(
            frame,
            "Info",
            self.show_info,
        )

        tk.Frame(
            frame,
            width=12,
        ).pack(
            side="left",
        )

        self.up_button = (
            self._toolbar_button(
                frame,
                "Up",
                self.go_up,
            )
        )
        self.refresh_button = (
            self._toolbar_button(
                frame,
                "Refresh",
                self.refresh,
            )
        )

    def _build_address_bar(self):
        frame = tk.Frame(
            self.root,
            padx=7,
            pady=5,
        )
        frame.pack(
            fill="x",
        )

        tk.Label(
            frame,
            text="Archive:",
        ).pack(
            side="left",
        )

        archive_entry = tk.Entry(
            frame,
            textvariable=self.path_var,
            state="readonly",
            relief="sunken",
            bd=1,
        )
        archive_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(
                5,
                8,
            ),
        )

        tk.Label(
            frame,
            text="Path:",
        ).pack(
            side="left",
        )

        folder_entry = tk.Entry(
            frame,
            textvariable=self.folder_var,
            state="readonly",
            width=28,
            relief="sunken",
            bd=1,
        )
        folder_entry.pack(
            side="left",
            padx=(
                5,
                0,
            ),
        )

    def _build_file_list(self):
        container = tk.Frame(
            self.root,
            bd=1,
            relief="sunken",
        )
        container.pack(
            fill="both",
            expand=True,
            padx=7,
            pady=(
                0,
                6,
            ),
        )

        columns = (
            "size",
            "packed",
            "type",
            "modified",
            "crc",
        )

        self.tree = ttk.Treeview(
            container,
            columns=columns,
            show="tree headings",
            selectmode="extended",
        )

        self.tree.heading(
            "#0",
            text="Name",
        )
        self.tree.heading(
            "size",
            text="Size",
        )
        self.tree.heading(
            "packed",
            text="Packed",
        )
        self.tree.heading(
            "type",
            text="Type",
        )
        self.tree.heading(
            "modified",
            text="Modified",
        )
        self.tree.heading(
            "crc",
            text="CRC",
        )

        self.tree.column(
            "#0",
            width=300,
            minwidth=180,
        )
        self.tree.column(
            "size",
            width=95,
            anchor="e",
        )
        self.tree.column(
            "packed",
            width=95,
            anchor="e",
        )
        self.tree.column(
            "type",
            width=105,
        )
        self.tree.column(
            "modified",
            width=145,
        )
        self.tree.column(
            "crc",
            width=95,
        )

        y_scroll = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self.tree.yview,
        )
        x_scroll = ttk.Scrollbar(
            container,
            orient="horizontal",
            command=self.tree.xview,
        )

        self.tree.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        y_scroll.grid(
            row=0,
            column=1,
            sticky="ns",
        )
        x_scroll.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        container.grid_rowconfigure(
            0,
            weight=1,
        )
        container.grid_columnconfigure(
            0,
            weight=1,
        )

        self.tree.bind(
            "<Double-1>",
            self.on_double_click,
        )
        self.tree.bind(
            "<Return>",
            self.on_double_click,
        )
        self.tree.bind(
            "<Button-3>",
            self.on_right_click,
        )

        self.context_menu = tk.Menu(
            self.tree,
            tearoff=False,
        )
        self.context_menu.add_command(
            label="Extract selected...",
            command=self.extract_selected,
        )
        self.context_menu.add_command(
            label="Open",
            command=self.open_selected,
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Delete selected",
            command=self.delete_selected,
        )
        self.context_menu.add_command(
            label="Properties",
            command=self.show_selected_info,
        )

    def _build_status_bar(self):
        label = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            bd=1,
            relief="sunken",
            padx=6,
            pady=3,
        )
        label.pack(
            fill="x",
            side="bottom",
        )

    def _need_archive(self):
        if (
            self.archive_path
            and self.archive_path.is_file()
        ):
            return True

        messagebox.showinfo(
            "UwUConverter Archive Manager",
            "Open an archive first.",
            parent=self.root,
        )
        return False

    def choose_archive(self):
        selected = filedialog.askopenfilename(
            title="Open archive",
            filetypes=ARCHIVE_FILE_TYPES,
            parent=self.root,
        )

        if selected:
            self.open_archive(
                selected
            )

    def open_archive(
        self,
        path,
    ):
        archive = (
            pathlib.Path(
                path
            )
            .expanduser()
            .resolve()
        )

        if not archive.is_file():
            messagebox.showerror(
                "UwUConverter Archive Manager",
                (
                    "Archive does not exist:\n\n"
                    + str(archive)
                ),
                parent=self.root,
            )
            return

        self.archive_path = archive
        self.current_folder = ""
        self.root.title(
            archive.name
            + " - UwUConverter Archive Manager"
        )
        self.path_var.set(
            str(archive)
        )

        self.refresh()

    def close_archive(self):
        self.archive_path = None
        self.entries = []
        self.current_folder = ""
        self.item_map = {}
        self.path_var.set(
            "No archive open"
        )
        self.folder_var.set(
            "/"
        )
        self.root.title(
            "UwUConverter Archive Manager"
        )

        for item in self.tree.get_children():
            self.tree.delete(
                item
            )

        self.status_var.set(
            "Ready"
        )

    def new_archive(self):
        output = filedialog.asksaveasfilename(
            title="Create archive",
            defaultextension=".zip",
            initialfile="Archive.zip",
            filetypes=[
                (
                    "ZIP archive",
                    "*.zip",
                ),
                (
                    "7-Zip archive",
                    "*.7z",
                ),
            ],
            parent=self.root,
        )

        if not output:
            return

        inputs = filedialog.askopenfilenames(
            title="Select files for the new archive",
            parent=self.root,
        )

        if not inputs:
            return

        try:
            archive = create_archive(
                output,
                inputs,
                force=(
                    pathlib.Path(
                        output
                    ).exists()
                ),
                working_directory=(
                    pathlib.Path(
                        inputs[0]
                    ).resolve().parent
                    if all(
                        pathlib.Path(path).resolve().parent
                        == pathlib.Path(inputs[0]).resolve().parent
                        for path in inputs
                    )
                    else None
                ),
            )
        except Exception as error:
            self._show_error(
                error
            )
            return

        self.open_archive(
            archive
        )

    def refresh(self):
        if not self._need_archive():
            return

        try:
            self.status_var.set(
                "Reading archive..."
            )
            self.root.update_idletasks()

            self.entries = (
                list_archive_entries(
                    self.archive_path
                )
            )

            self._populate_current_folder()
        except Exception as error:
            self._show_error(
                error
            )

    def _populate_current_folder(self):
        self.item_map = {}

        for item in self.tree.get_children():
            self.tree.delete(
                item
            )

        prefix = (
            self.current_folder.rstrip("/")
            + "/"
            if self.current_folder
            else ""
        )

        visible = {}

        for entry in self.entries:
            full_path = (
                entry["path"]
                .replace(
                    "\\",
                    "/",
                )
                .strip("/")
            )

            if prefix:
                if not full_path.startswith(
                    prefix
                ):
                    continue

                relative = full_path[
                    len(prefix):
                ]
            else:
                relative = full_path

            if not relative:
                continue

            parts = relative.split(
                "/"
            )

            if len(parts) > 1:
                name = parts[0]
                synthetic_path = (
                    prefix
                    + name
                ).strip("/")

                existing = visible.get(
                    name
                )

                if existing is None:
                    visible[name] = {
                        "path": synthetic_path,
                        "folder": True,
                        "size": 0,
                        "packed_size": 0,
                        "modified": "",
                        "crc": "",
                        "method": "",
                        "encrypted": False,
                    }

                continue

            visible[
                parts[0]
            ] = entry

        if self.current_folder:
            iid = self.tree.insert(
                "",
                "end",
                text="..",
                values=(
                    "",
                    "",
                    "Folder",
                    "",
                    "",
                ),
            )
            self.item_map[
                iid
            ] = {
                "up": True,
                "folder": True,
                "path": "",
            }

        folder_items = []
        file_items = []

        for name, entry in visible.items():
            if entry.get(
                "folder"
            ):
                folder_items.append(
                    (
                        name,
                        entry,
                    )
                )
            else:
                file_items.append(
                    (
                        name,
                        entry,
                    )
                )

        folder_items.sort(
            key=lambda item: item[0].casefold()
        )
        file_items.sort(
            key=lambda item: item[0].casefold()
        )

        for name, entry in (
            folder_items
            + file_items
        ):
            is_folder = bool(
                entry.get(
                    "folder"
                )
            )

            if is_folder:
                type_text = "Folder"
                size_text = ""
                packed_text = ""
            else:
                suffix = (
                    pathlib.PurePosixPath(
                        name
                    ).suffix
                )
                type_text = (
                    suffix[1:].upper()
                    + " file"
                    if suffix
                    else "File"
                )
                size_text = _format_size(
                    entry.get(
                        "size",
                        0,
                    )
                )
                packed_text = _format_size(
                    entry.get(
                        "packed_size",
                        0,
                    )
                )

            iid = self.tree.insert(
                "",
                "end",
                text=name,
                values=(
                    size_text,
                    packed_text,
                    type_text,
                    entry.get(
                        "modified",
                        "",
                    ),
                    entry.get(
                        "crc",
                        "",
                    ),
                ),
            )

            self.item_map[
                iid
            ] = entry

        self.folder_var.set(
            "/"
            + self.current_folder
            if self.current_folder
            else "/"
        )

        file_count = sum(
            1
            for entry in self.entries
            if not entry.get(
                "folder"
            )
        )
        folder_count = sum(
            1
            for entry in self.entries
            if entry.get(
                "folder"
            )
        )
        total_size = sum(
            int(
                entry.get(
                    "size",
                    0,
                )
            )
            for entry in self.entries
            if not entry.get(
                "folder"
            )
        )

        self.status_var.set(
            (
                str(file_count)
                + " files, "
                + str(folder_count)
                + " folders, "
                + _format_size(
                    total_size
                )
            )
        )

    def selected_entries(self):
        result = []

        for iid in self.tree.selection():
            entry = self.item_map.get(
                iid
            )

            if not entry:
                continue

            if entry.get(
                "up"
            ):
                continue

            result.append(
                entry
            )

        return result

    def selected_paths(self):
        return [
            entry["path"]
            for entry in self.selected_entries()
            if entry.get(
                "path"
            )
        ]

    def go_up(self):
        if not self.current_folder:
            return

        parent = pathlib.PurePosixPath(
            self.current_folder
        ).parent

        self.current_folder = (
            ""
            if str(parent) == "."
            else str(parent)
        )

        self._populate_current_folder()

    def on_double_click(
        self,
        _event=None,
    ):
        self.open_selected()

    def open_selected(self):
        selection = (
            self.tree.selection()
        )

        if not selection:
            return

        entry = self.item_map.get(
            selection[0]
        )

        if not entry:
            return

        if entry.get(
            "up"
        ):
            self.go_up()
            return

        if entry.get(
            "folder"
        ):
            self.current_folder = (
                entry["path"]
                .strip("/")
            )
            self._populate_current_folder()
            return

        self._extract_and_open(
            entry["path"]
        )

    def _extract_and_open(
        self,
        entry_path,
    ):
        if not self._need_archive():
            return

        temp_root = pathlib.Path(
            tempfile.mkdtemp(
                prefix="UwUConverter-archive-open-"
            )
        )

        try:
            extract_archive_entries(
                self.archive_path,
                [
                    entry_path
                ],
                temp_root,
                password=self.password,
            )

            extracted = (
                temp_root
                / pathlib.PurePosixPath(
                    entry_path
                )
            )

            if extracted.exists():
                _open_path(
                    extracted
                )
            else:
                _open_path(
                    temp_root
                )

        except Exception as error:
            self._show_error(
                error
            )

    def extract_selected(self):
        if not self._need_archive():
            return

        output = filedialog.askdirectory(
            title="Extract to",
            initialdir=str(
                self.archive_path.parent
            ),
            parent=self.root,
        )

        if not output:
            return

        selected = (
            self.selected_paths()
        )

        try:
            extract_archive_entries(
                self.archive_path,
                selected,
                output,
                password=self.password,
            )

            messagebox.showinfo(
                "UwUConverter Archive Manager",
                (
                    "Extraction finished.\n\n"
                    + output
                ),
                parent=self.root,
            )

        except Exception as error:
            self._show_error(
                error
            )

    def add_files(self):
        if not self._need_archive():
            return

        selected = filedialog.askopenfilenames(
            title="Add files to archive",
            initialdir=str(
                self.archive_path.parent
            ),
            parent=self.root,
        )

        if not selected:
            return

        self._add_paths(
            selected
        )

    def add_folder(self):
        if not self._need_archive():
            return

        selected = filedialog.askdirectory(
            title="Add folder to archive",
            initialdir=str(
                self.archive_path.parent
            ),
            parent=self.root,
        )

        if not selected:
            return

        self._add_paths(
            [
                selected
            ]
        )

    def _add_paths(
        self,
        selected,
    ):
        paths = [
            pathlib.Path(
                path
            ).resolve()
            for path in selected
        ]

        same_parent = all(
            path.parent
            == paths[0].parent
            for path in paths
        )

        try:
            add_to_archive(
                self.archive_path,
                paths,
                working_directory=(
                    paths[0].parent
                    if same_parent
                    else None
                ),
            )
            self.refresh()

        except Exception as error:
            self._show_error(
                error
            )

    def delete_selected(self):
        if not self._need_archive():
            return

        selected = (
            self.selected_paths()
        )

        if not selected:
            messagebox.showinfo(
                "UwUConverter Archive Manager",
                "Select one or more archive entries first.",
                parent=self.root,
            )
            return

        if not messagebox.askyesno(
            "Delete from archive?",
            (
                "Remove "
                + str(len(selected))
                + " selected item(s) from the archive?"
            ),
            parent=self.root,
        ):
            return

        try:
            delete_archive_entries(
                self.archive_path,
                selected,
            )
            self.refresh()

        except Exception as error:
            self._show_error(
                error
            )

    def test_current_archive(self):
        if not self._need_archive():
            return

        try:
            self.status_var.set(
                "Testing archive..."
            )
            self.root.update_idletasks()

            test_archive(
                self.archive_path,
                password=self.password,
            )

            self.status_var.set(
                "Archive test completed successfully."
            )

            messagebox.showinfo(
                "UwUConverter Archive Manager",
                "No archive errors were reported by 7-Zip.",
                parent=self.root,
            )

        except Exception as error:
            self._show_error(
                error
            )

    def set_password(self):
        password = simpledialog.askstring(
            "Archive password",
            (
                "Password used when extracting or testing "
                "encrypted archive entries:"
            ),
            show="*",
            parent=self.root,
        )

        if password is None:
            return

        self.password = password

        self.status_var.set(
            (
                "Extraction password is set."
                if password
                else "Extraction password cleared."
            )
        )

    def clear_password(self):
        self.password = None
        self.status_var.set(
            "Extraction password cleared."
        )

    def show_info(self):
        if not self._need_archive():
            return

        file_count = sum(
            1
            for entry in self.entries
            if not entry.get(
                "folder"
            )
        )
        folder_count = sum(
            1
            for entry in self.entries
            if entry.get(
                "folder"
            )
        )
        unpacked = sum(
            int(
                entry.get(
                    "size",
                    0,
                )
            )
            for entry in self.entries
            if not entry.get(
                "folder"
            )
        )
        packed_entries = sum(
            int(
                entry.get(
                    "packed_size",
                    0,
                )
            )
            for entry in self.entries
            if not entry.get(
                "folder"
            )
        )

        actual_size = (
            self.archive_path.stat().st_size
        )

        messagebox.showinfo(
            "Archive information",
            (
                "Archive:\n"
                + str(self.archive_path)
                + "\n\nFiles: "
                + str(file_count)
                + "\nFolders: "
                + str(folder_count)
                + "\nUnpacked size: "
                + _format_size(
                    unpacked
                )
                + "\nPacked entries: "
                + _format_size(
                    packed_entries
                )
                + "\nArchive file size: "
                + _format_size(
                    actual_size
                )
            ),
            parent=self.root,
        )

    def show_selected_info(self):
        selected = (
            self.selected_entries()
        )

        if not selected:
            self.show_info()
            return

        entry = selected[0]

        messagebox.showinfo(
            "Entry information",
            (
                "Path: "
                + entry.get(
                    "path",
                    "",
                )
                + "\nType: "
                + (
                    "Folder"
                    if entry.get(
                        "folder"
                    )
                    else "File"
                )
                + "\nSize: "
                + _format_size(
                    entry.get(
                        "size",
                        0,
                    )
                )
                + "\nPacked: "
                + _format_size(
                    entry.get(
                        "packed_size",
                        0,
                    )
                )
                + "\nModified: "
                + entry.get(
                    "modified",
                    "",
                )
                + "\nCRC: "
                + entry.get(
                    "crc",
                    "",
                )
                + "\nMethod: "
                + entry.get(
                    "method",
                    "",
                )
                + "\nEncrypted: "
                + (
                    "Yes"
                    if entry.get(
                        "encrypted"
                    )
                    else "No"
                )
            ),
            parent=self.root,
        )

    def show_about(self):
        messagebox.showinfo(
            "About UwUConverter Archive Manager",
            (
                "UwUConverter Archive Manager\n\n"
                "A WinRAR-style archive browser powered by 7-Zip.\n"
                "It uses UwUConverter's existing archive backend."
            ),
            parent=self.root,
        )

    def on_right_click(
        self,
        event,
    ):
        iid = self.tree.identify_row(
            event.y
        )

        if iid:
            if iid not in self.tree.selection():
                self.tree.selection_set(
                    iid
                )

        try:
            self.context_menu.tk_popup(
                event.x_root,
                event.y_root,
            )
        finally:
            self.context_menu.grab_release()

    def _show_error(
        self,
        error,
    ):
        self.status_var.set(
            "Operation failed."
        )
        messagebox.showerror(
            "UwUConverter Archive Manager",
            str(error),
            parent=self.root,
        )


def open_archive_manager(
    archive_path=None,
):
    root = tk.Tk()

    ArchiveManagerWindow(
        root,
        archive_path=archive_path,
    )

    root.mainloop()


def main():
    archive = (
        sys.argv[1]
        if len(sys.argv) > 1
        else None
    )

    open_archive_manager(
        archive
    )


if __name__ == "__main__":
    main()
