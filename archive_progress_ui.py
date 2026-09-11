import os
import pathlib
import queue
import shutil
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from archive_manager import (
    ArchiveOperationCancelled,
    add_to_archive,
    archive_layout_summary,
    create_archive,
    extract_archive_entries,
    extract_archive_with_options,
)


def _open_path(
    path,
):
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


class ArchiveProgressWindow:
    def __init__(
        self,
        window,
        jobs,
        title,
        owns_root,
    ):
        self.window = window
        self.jobs = jobs
        self.title = title
        self.owns_root = owns_root

        self.events = queue.Queue()
        self.cancel_event = (
            threading.Event()
        )
        self.success = False
        self.finished = False
        self.started_at = None
        self.row_ids = []
        self.open_targets = []

        self.current_name = (
            tk.StringVar(
                value="Preparing..."
            )
        )
        self.detail = tk.StringVar(
            value=""
        )
        self.current_percent = (
            tk.DoubleVar(
                value=0
            )
        )
        self.overall_percent = (
            tk.DoubleVar(
                value=0
            )
        )
        self.counter = tk.StringVar(
            value=(
                "0 of "
                + str(
                    len(jobs)
                )
            )
        )
        self.elapsed = tk.StringVar(
            value="Elapsed: 0s"
        )

        self.window.title(
            title
        )
        self.window.geometry(
            "720x470"
        )
        self.window.minsize(
            620,
            390,
        )
        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.on_close,
        )

        self._build_ui()

    def _build_ui(self):
        outer = ttk.Frame(
            self.window,
            padding=18,
        )
        outer.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            outer,
            text=self.title,
            font=(
                "TkDefaultFont",
                16,
                "bold",
            ),
        ).pack(
            anchor="w",
        )

        ttk.Label(
            outer,
            textvariable=self.current_name,
            font=(
                "TkDefaultFont",
                11,
                "bold",
            ),
        ).pack(
            anchor="w",
            pady=(
                14,
                2,
            ),
        )

        ttk.Label(
            outer,
            textvariable=self.detail,
        ).pack(
            anchor="w",
        )

        ttk.Label(
            outer,
            text="Current operation",
        ).pack(
            anchor="w",
            pady=(
                12,
                3,
            ),
        )

        self.current_bar = (
            ttk.Progressbar(
                outer,
                maximum=100,
                variable=self.current_percent,
            )
        )
        self.current_bar.pack(
            fill="x",
        )

        overall_header = ttk.Frame(
            outer
        )
        overall_header.pack(
            fill="x",
            pady=(
                12,
                3,
            ),
        )

        ttk.Label(
            overall_header,
            text=(
                "Overall progress"
                if len(self.jobs) > 1
                else "Progress"
            ),
        ).pack(
            side="left",
        )

        ttk.Label(
            overall_header,
            textvariable=self.counter,
        ).pack(
            side="right",
        )

        self.overall_bar = (
            ttk.Progressbar(
                outer,
                maximum=100,
                variable=self.overall_percent,
            )
        )
        self.overall_bar.pack(
            fill="x",
        )

        queue_frame = ttk.LabelFrame(
            outer,
            text=(
                "Files"
                if len(self.jobs) > 1
                else "Operation"
            ),
            padding=6,
        )
        queue_frame.pack(
            fill="both",
            expand=True,
            pady=(
                14,
                8,
            ),
        )

        self.tree = ttk.Treeview(
            queue_frame,
            columns=(
                "operation",
                "status",
            ),
            show="headings",
            height=7,
        )
        self.tree.heading(
            "operation",
            text="Item",
        )
        self.tree.heading(
            "status",
            text="Status",
        )
        self.tree.column(
            "operation",
            width=470,
        )
        self.tree.column(
            "status",
            width=140,
            anchor="center",
        )

        scrollbar = ttk.Scrollbar(
            queue_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(
            yscrollcommand=scrollbar.set,
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
        )
        scrollbar.pack(
            side="right",
            fill="y",
        )

        for job in self.jobs:
            row = self.tree.insert(
                "",
                "end",
                values=(
                    job[
                        "display_name"
                    ],
                    "Waiting",
                ),
            )
            self.row_ids.append(
                row
            )

        bottom = ttk.Frame(
            outer
        )
        bottom.pack(
            fill="x",
        )

        ttk.Label(
            bottom,
            textvariable=self.elapsed,
        ).pack(
            side="left",
        )

        self.close_button = ttk.Button(
            bottom,
            text="Close",
            command=self.on_close,
            state="disabled",
        )
        self.close_button.pack(
            side="right",
        )

        self.cancel_button = ttk.Button(
            bottom,
            text="Cancel",
            command=self.cancel,
        )
        self.cancel_button.pack(
            side="right",
            padx=(
                0,
                8,
            ),
        )

        self.open_button = ttk.Button(
            bottom,
            text="Open Folder",
            command=self.open_result,
            state="disabled",
        )
        self.open_button.pack(
            side="right",
            padx=(
                0,
                8,
            ),
        )

    def _confirm_extract_here_layout(
        self,
    ):
        risky = []

        for job in self.jobs:
            if (
                job["kind"]
                != "extract"
                or not job.get(
                    "extract_here"
                )
            ):
                continue

            try:
                summary = archive_layout_summary(
                    job["archive"]
                )
                job[
                    "entry_metadata"
                ] = summary[
                    "entries"
                ]

            except Exception:
                # Extraction itself will report the real error.
                continue

            if not summary[
                "scatters_on_extract_here"
            ]:
                continue

            risky.append(
                (
                    pathlib.Path(
                        job["archive"]
                    ).name,
                    summary[
                        "top_level_count"
                    ],
                    summary[
                        "top_level_names"
                    ][:5],
                )
            )

        if not risky:
            return True

        lines = []

        for name, count, names in risky[:6]:
            preview = ", ".join(
                names
            )

            if count > len(
                names
            ):
                preview += ", ..."

            lines.append(
                (
                    "• "
                    + name
                    + " - "
                    + str(count)
                    + " top-level items"
                    + (
                        ": "
                        + preview
                        if preview
                        else ""
                    )
                )
            )

        if len(risky) > 6:
            lines.append(
                "• ...and "
                + str(
                    len(risky) - 6
                )
                + " more archives"
            )

        return messagebox.askyesno(
            "Extract directly here?",
            (
                "Some selected archives do not contain one "
                "single folder holding everything.\n\n"
                "Extracting them here will place multiple files/folders "
                "directly into the current directory:\n\n"
                + "\n".join(
                    lines
                )
                + "\n\nContinue extracting here?"
            ),
            parent=self.window,
        )

    def start(self):
        self.window.update_idletasks()

        if not self._confirm_extract_here_layout():
            self.finished = True
            self.current_name.set(
                "Cancelled"
            )
            self.detail.set(
                "Nothing was extracted."
            )
            self.cancel_button.configure(
                state="disabled"
            )
            self.close_button.configure(
                state="normal"
            )
            return

        self.started_at = time.monotonic()

        worker = threading.Thread(
            target=self._worker,
            daemon=True,
        )
        worker.start()

        self.window.after(
            80,
            self._poll,
        )
        self.window.after(
            500,
            self._update_elapsed,
        )

    def _progress_callback(
        self,
        index,
        percent,
        detail,
    ):
        self.events.put(
            (
                "progress",
                index,
                percent,
                detail,
            )
        )

    def _worker(self):
        failures = []

        for index, job in enumerate(
            self.jobs
        ):
            if self.cancel_event.is_set():
                break

            self.events.put(
                (
                    "start_job",
                    index,
                )
            )

            try:
                callback = (
                    lambda percent, detail, job_index=index:
                    self._progress_callback(
                        job_index,
                        percent,
                        detail,
                    )
                )

                kind = job["kind"]

                if kind == "create":
                    create_archive(
                        job["archive"],
                        job["inputs"],
                        archive_format=job.get(
                            "archive_format"
                        ),
                        level=job.get(
                            "level",
                            5,
                        ),
                        password=job.get(
                            "password"
                        ),
                        encrypt_headers=job.get(
                            "encrypt_headers",
                            False,
                        ),
                        force=job.get(
                            "force",
                            False,
                        ),
                        working_directory=job.get(
                            "working_directory"
                        ),
                        progress_callback=callback,
                        cancel_event=self.cancel_event,
                    )

                    self.open_targets.append(
                        pathlib.Path(
                            job["archive"]
                        ).parent
                    )

                elif kind == "extract":
                    output = (
                        extract_archive_with_options(
                            job["archive"],
                            output_dir=job.get(
                                "output_dir"
                            ),
                            password=job.get(
                                "password"
                            ),
                            overwrite=job.get(
                                "overwrite",
                                True,
                            ),
                            delete_source=job.get(
                                "delete_source",
                                False,
                            ),
                            progress_callback=callback,
                            cancel_event=self.cancel_event,
                            entry_metadata=job.get(
                                "entry_metadata"
                            ),
                            refresh_timestamps=True,
                        )
                    )

                    self.open_targets.append(
                        output
                        if pathlib.Path(
                            output
                        ).is_dir()
                        else pathlib.Path(
                            output
                        ).parent
                    )

                elif kind == "extract_entries":
                    output = extract_archive_entries(
                        job["archive"],
                        job.get(
                            "entry_paths",
                            [],
                        ),
                        job["output_dir"],
                        password=job.get(
                            "password"
                        ),
                        overwrite=job.get(
                            "overwrite",
                            True,
                        ),
                        progress_callback=callback,
                        cancel_event=self.cancel_event,
                        refresh_timestamps=True,
                    )

                    self.open_targets.append(
                        output
                    )

                elif kind == "add":
                    add_to_archive(
                        job["archive"],
                        job["inputs"],
                        working_directory=job.get(
                            "working_directory"
                        ),
                        progress_callback=callback,
                        cancel_event=self.cancel_event,
                    )

                    self.open_targets.append(
                        pathlib.Path(
                            job["archive"]
                        ).parent
                    )

                else:
                    raise ValueError(
                        "Unknown archive job kind: "
                        + str(kind)
                    )

                self.events.put(
                    (
                        "job_done",
                        index,
                    )
                )

            except ArchiveOperationCancelled:
                self.cancel_event.set()
                self.events.put(
                    (
                        "job_cancelled",
                        index,
                    )
                )
                break

            except Exception as error:
                failures.append(
                    (
                        index,
                        str(error),
                    )
                )
                self.events.put(
                    (
                        "job_failed",
                        index,
                        str(error),
                    )
                )

        self.events.put(
            (
                "finished",
                failures,
                self.cancel_event.is_set(),
            )
        )

    def _poll(self):
        try:
            while True:
                event = (
                    self.events.get_nowait()
                )
                kind = event[0]

                if kind == "start_job":
                    index = event[1]
                    self._show_job_started(
                        index
                    )

                elif kind == "progress":
                    _, index, percent, detail = event
                    self._show_progress(
                        index,
                        percent,
                        detail,
                    )

                elif kind == "job_done":
                    index = event[1]
                    self.tree.set(
                        self.row_ids[index],
                        "status",
                        "Done",
                    )

                elif kind == "job_failed":
                    _, index, error = event
                    self.tree.set(
                        self.row_ids[index],
                        "status",
                        "Failed",
                    )
                    self.detail.set(
                        error.splitlines()[0][
                            :220
                        ]
                    )

                elif kind == "job_cancelled":
                    index = event[1]
                    self.tree.set(
                        self.row_ids[index],
                        "status",
                        "Cancelled",
                    )

                elif kind == "finished":
                    _, failures, cancelled = event
                    self._finish(
                        failures,
                        cancelled,
                    )

        except queue.Empty:
            pass

        if not self.finished:
            self.window.after(
                80,
                self._poll,
            )

    def _show_job_started(
        self,
        index,
    ):
        job = self.jobs[
            index
        ]

        self.current_name.set(
            job[
                "display_name"
            ]
        )
        self.detail.set(
            job.get(
                "detail",
                "",
            )
        )
        self.current_percent.set(
            0
        )
        self.counter.set(
            (
                str(index + 1)
                + " of "
                + str(
                    len(self.jobs)
                )
            )
        )

        self.tree.set(
            self.row_ids[index],
            "status",
            "Working",
        )
        self.tree.see(
            self.row_ids[index]
        )

    def _show_progress(
        self,
        index,
        percent,
        detail,
    ):
        self.current_percent.set(
            percent
        )

        overall = (
            (
                index
                + percent / 100.0
            )
            / max(
                1,
                len(self.jobs)
            )
            * 100.0
        )

        self.overall_percent.set(
            overall
        )

        if detail:
            self.detail.set(
                detail
            )

        self.tree.set(
            self.row_ids[index],
            "status",
            str(percent) + "%",
        )

    def _finish(
        self,
        failures,
        cancelled,
    ):
        self.finished = True

        if cancelled:
            self.success = False
            self.current_name.set(
                "Cancelled"
            )
            self.detail.set(
                "The current archive operation was stopped."
            )

            for index, row in enumerate(
                self.row_ids
            ):
                if self.tree.set(
                    row,
                    "status"
                ) == "Waiting":
                    self.tree.set(
                        row,
                        "status",
                        "Cancelled",
                    )

        elif failures:
            self.success = False
            self.current_name.set(
                "Finished with errors"
            )
            self.detail.set(
                str(
                    len(failures)
                )
                + " operation(s) failed. "
                + "See the queue above."
            )

        else:
            self.success = True
            self.current_name.set(
                "Complete"
            )
            self.detail.set(
                (
                    "All archive operations completed successfully."
                    if len(self.jobs) > 1
                    else "Archive operation completed successfully."
                )
            )
            self.current_percent.set(
                100
            )
            self.overall_percent.set(
                100
            )

        self.cancel_button.configure(
            state="disabled"
        )
        self.close_button.configure(
            state="normal"
        )

        if self.open_targets:
            self.open_button.configure(
                state="normal"
            )

    def _update_elapsed(self):
        if (
            self.started_at is not None
            and not self.finished
        ):
            elapsed = int(
                time.monotonic()
                - self.started_at
            )
            minutes, seconds = divmod(
                elapsed,
                60,
            )

            if minutes:
                text = (
                    "Elapsed: "
                    + str(minutes)
                    + "m "
                    + str(seconds)
                    + "s"
                )
            else:
                text = (
                    "Elapsed: "
                    + str(seconds)
                    + "s"
                )

            self.elapsed.set(
                text
            )

            self.window.after(
                500,
                self._update_elapsed,
            )

    def cancel(self):
        if self.finished:
            return

        self.cancel_event.set()
        self.cancel_button.configure(
            state="disabled"
        )
        self.current_name.set(
            "Cancelling..."
        )
        self.detail.set(
            "Waiting for 7-Zip to stop safely."
        )

    def open_result(self):
        if not self.open_targets:
            return

        try:
            _open_path(
                self.open_targets[0]
            )
        except Exception as error:
            messagebox.showerror(
                "UwUConverter",
                str(error),
                parent=self.window,
            )

    def on_close(self):
        if not self.finished:
            if not messagebox.askyesno(
                "Cancel archive operation?",
                (
                    "An archive operation is still running.\n\n"
                    "Cancel it and close this window?"
                ),
                parent=self.window,
            ):
                return

            self.cancel()
            return

        self.window.destroy()


def _show_jobs(
    jobs,
    title,
    parent=None,
):
    owns_root = parent is None

    if owns_root:
        window = tk.Tk()
    else:
        window = tk.Toplevel(
            parent
        )
        window.transient(
            parent
        )

    dialog = ArchiveProgressWindow(
        window,
        jobs,
        title,
        owns_root,
    )

    dialog.start()

    if owns_root:
        window.mainloop()
    else:
        parent.wait_window(
            window
        )

    return dialog.success


def show_create_archive_progress(
    archive_path,
    input_paths,
    *,
    archive_format=None,
    level=5,
    password=None,
    encrypt_headers=False,
    force=False,
    working_directory=None,
    parent=None,
):
    archive = pathlib.Path(
        archive_path
    )

    inputs = [
        str(path)
        for path in input_paths
    ]

    job = {
        "kind": "create",
        "archive": str(archive),
        "inputs": inputs,
        "archive_format": archive_format,
        "level": level,
        "password": password,
        "encrypt_headers": encrypt_headers,
        "force": force,
        "working_directory": (
            str(
                working_directory
            )
            if working_directory is not None
            else None
        ),
        "display_name": (
            "Creating "
            + archive.name
        ),
        "detail": (
            str(
                len(inputs)
            )
            + " selected item(s)"
        ),
    }

    return _show_jobs(
        [job],
        "Compressing files",
        parent=parent,
    )


def show_extract_archives_progress(
    archive_paths,
    action,
    *,
    password=None,
    parent=None,
):
    action = action.lower()

    actions = {
        "archive_extract_here": (
            False,
            False,
        ),
        "archive_extract_folder": (
            True,
            False,
        ),
        "archive_extract_here_delete": (
            False,
            True,
        ),
        "archive_extract_folder_delete": (
            True,
            True,
        ),
    }

    if action not in actions:
        raise ValueError(
            "Unknown archive extraction action: "
            + action
        )

    into_folder, delete_source = (
        actions[action]
    )

    jobs = []

    for raw_path in archive_paths:
        archive = (
            pathlib.Path(
                raw_path
            )
            .expanduser()
            .resolve()
        )

        output_dir = (
            None
            if into_folder
            else archive.parent
        )

        jobs.append(
            {
                "kind": "extract",
                "archive": str(
                    archive
                ),
                "output_dir": (
                    str(output_dir)
                    if output_dir is not None
                    else None
                ),
                "extract_here": (
                    not into_folder
                ),
                "delete_source": delete_source,
                "password": password,
                "display_name": (
                    "Extracting "
                    + archive.name
                ),
                "detail": (
                    "Extract to archive-named folder"
                    if into_folder
                    else "Extract directly here"
                ),
            }
        )

    return _show_jobs(
        jobs,
        (
            "Extracting archives"
            if len(jobs) > 1
            else "Extracting archive"
        ),
        parent=parent,
    )


def show_extract_entries_progress(
    archive_path,
    entry_paths,
    output_dir,
    *,
    password=None,
    parent=None,
):
    archive = pathlib.Path(
        archive_path
    )

    entries = [
        str(path)
        for path in entry_paths
    ]

    job = {
        "kind": "extract_entries",
        "archive": str(
            archive
        ),
        "entry_paths": entries,
        "output_dir": str(
            output_dir
        ),
        "password": password,
        "display_name": (
            "Extracting "
            + archive.name
        ),
        "detail": (
            str(
                len(entries)
            )
            + " selected archive item(s)"
            if entries
            else "Extracting the whole archive"
        ),
    }

    return _show_jobs(
        [job],
        "Extracting archive",
        parent=parent,
    )


def show_add_to_archive_progress(
    archive_path,
    input_paths,
    *,
    working_directory=None,
    parent=None,
):
    archive = pathlib.Path(
        archive_path
    )

    inputs = [
        str(path)
        for path in input_paths
    ]

    job = {
        "kind": "add",
        "archive": str(
            archive
        ),
        "inputs": inputs,
        "working_directory": (
            str(
                working_directory
            )
            if working_directory is not None
            else None
        ),
        "display_name": (
            "Updating "
            + archive.name
        ),
        "detail": (
            "Adding "
            + str(
                len(inputs)
            )
            + " item(s)"
        ),
    }

    return _show_jobs(
        [job],
        "Adding files to archive",
        parent=parent,
    )
