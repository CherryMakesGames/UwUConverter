import argparse
import os
import pathlib
import queue
import shlex
import shutil
import subprocess
import sys
import threading


APP_NAME = "UwUConverter"


BROWSERS = [
    {         
        "id": "chrome",
        "name": "Google Chrome",
        "family": "chromium",
        "manager": "chrome://extensions",
        "commands": [
            "google-chrome",
            "google-chrome-stable",
        ], 
        "flatpaks": [
            "com.google.Chrome",
        ],
    },
    {
        "id": "chromium",
        "name": "Chromium",
        "family": "chromium",
        "manager": "chrome://extensions",
        "commands": [
            "chromium",
            "chromium-browser",
        ],
        "flatpaks": [
            "org.chromium.Chromium",
        ],
    },
    {
        "id": "edge",
        "name": "Microsoft Edge",
        "family": "chromium",
        "manager": "edge://extensions",
        "commands": [
            "microsoft-edge",
            "microsoft-edge-stable",
            "microsoft-edge-beta",
            "microsoft-edge-dev",
        ],
        "flatpaks": [
            "com.microsoft.Edge",
        ],
    },
    {
        "id": "opera",
        "name": "Opera",
        "family": "chromium",
        "manager": "opera://extensions",
        "commands": [
            "opera",
            "opera-stable",
            "opera-beta",
            "opera-developer",
        ],
        "flatpaks": [
            "com.opera.Opera",
        ],
    },
    {
        "id": "opera-gx",
        "name": "Opera GX",
        "family": "chromium",
        "manager": "opera://extensions",
        "commands": [
            "opera-gx",
            "opera-gx-stable",
        ],
        "flatpaks": [
            "com.opera.opera-gx",
        ],
    },
    {
        "id": "brave",
        "name": "Brave",
        "family": "chromium",
        "manager": "brave://extensions",
        "commands": [
            "brave-browser",
            "brave-browser-stable",
            "brave",
        ],
        "flatpaks": [
            "com.brave.Browser",
        ],
    },
    {
        "id": "vivaldi",
        "name": "Vivaldi",
        "family": "chromium",
        "manager": "vivaldi://extensions",
        "commands": [
            "vivaldi",
            "vivaldi-stable",
            "vivaldi-snapshot",
        ],
        "flatpaks": [
            "com.vivaldi.Vivaldi",
        ],
    },
    {
        "id": "firefox",
        "name": "Firefox",
        "family": "firefox",
        "manager": "about:debugging#/runtime/this-firefox",
        "commands": [
            "firefox",
            "firefox-esr",
        ],
        "flatpaks": [
            "org.mozilla.firefox",
        ],
    },
]


def package_directory():
    if getattr(sys, "frozen", False):
        return pathlib.Path(
            sys.executable
        ).resolve().parent

    return pathlib.Path(
        __file__
    ).resolve().parent


def app_directory():
    root = pathlib.Path(
        os.environ.get(
            "XDG_DATA_HOME",
            pathlib.Path.home()
            / ".local"
            / "share",
        )
    )

    return root / APP_NAME


def cli_link_path():
    return (
        pathlib.Path.home()
        / ".local"
        / "bin"
        / "UwUConverter"
    )


def updater_autostart_path():
    root = pathlib.Path(
        os.environ.get(
            "XDG_CONFIG_HOME",
            pathlib.Path.home()
            / ".config",
        )
    )

    return (
        root
        / "autostart"
        / "uwuconverter-updater.desktop"
    )


def flatpak_installed(app_id):
    flatpak = shutil.which(
        "flatpak"
    )

    if not flatpak:
        return False

    try:
        result = subprocess.run(
            [
                flatpak,
                "info",
                app_id,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=4,
            check=False,
        )
    except (
        OSError,
        subprocess.TimeoutExpired,
    ):
        return False

    return result.returncode == 0


def detect_browsers():
    detected = []

    for definition in BROWSERS:
        browser = dict(
            definition
        )
        launch_command = None
        flatpak = False

        for command_name in definition[
            "commands"
        ]:
            executable = shutil.which(
                command_name
            )

            if executable:
                launch_command = [
                    executable
                ]
                break

        if launch_command is None:
            for app_id in definition[
                "flatpaks"
            ]:
                if flatpak_installed(
                    app_id
                ):
                    launch_command = [
                        shutil.which(
                            "flatpak"
                        )
                        or "flatpak",
                        "run",
                        app_id,
                    ]
                    flatpak = True
                    break

        if launch_command is None:
            continue

        browser[
            "launch_command"
        ] = launch_command
        browser[
            "flatpak"
        ] = flatpak

        detected.append(
            browser
        )

    return detected


def launch_browser(
    browser,
    target,
):
    command = list(
        browser[
            "launch_command"
        ]
    )

    command.append(
        target
    )

    subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )


def open_folder(path):
    opener = shutil.which(
        "xdg-open"
    )

    if not opener:
        return

    subprocess.Popen(
        [
            opener,
            str(path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )


def build_parser():
    parser = argparse.ArgumentParser(
        prog="UwUConverterInstaller",
    )

    parser.add_argument(
        "--update",
        action="store_true",
        help="Run in update mode.",
    )

    parser.add_argument(
        "--update-temp",
        default="",
        help=(
            "Temporary extracted update directory "
            "to remove after a successful update."
        ),
    )

    return parser


class InstallerWindow:
    def __init__(
        self,
        root,
        *,
        update_mode,
        update_temp,
    ):
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.root = root
        self.update_mode = update_mode
        self.update_temp = (
            pathlib.Path(
                update_temp
            ).resolve()
            if update_temp
            else None
        )

        self.package_dir = (
            package_directory()
        )
        self.install_script = (
            self.package_dir
            / "install.sh"
        )
        self.detected_browsers = (
            detect_browsers()
        )

        self.worker_queue = (
            queue.Queue()
        )
        self.install_finished = False
        self.install_succeeded = False
        self.cleanup_scheduled = False

        self.root.title(
            (
                "Update UwUConverter"
                if update_mode
                else "Install UwUConverter"
            )
        )
        self.root.geometry(
            "700x610"
            if not update_mode
            else "700x500"
        )
        self.root.minsize(
            620,
            450,
        )
        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close,
        )

        self.cli_var = tk.BooleanVar(
            value=(
                cli_link_path().exists()
                if update_mode
                else True
            )
        )
        self.updater_var = tk.BooleanVar(
            value=(
                updater_autostart_path().exists()
                if update_mode
                else True
            )
        )

        self.browser_vars = {}

        self.build_ui()
        self.root.after(
            100,
            self.poll_worker,
        )

    def build_ui(self):
        ttk = self.ttk

        outer = ttk.Frame(
            self.root,
            padding=22,
        )
        outer.pack(
            fill="both",
            expand=True,
        )

        title = ttk.Label(
            outer,
            text=(
                "Update UwUConverter"
                if self.update_mode
                else "Install UwUConverter"
            ),
            font=(
                "TkDefaultFont",
                16,
                "bold",
            ),
        )
        title.pack(
            anchor="w",
        )

        subtitle = ttk.Label(
            outer,
            text=(
                "The update will replace the installed files and "
                "refresh Linux file-manager and browser integrations."
                if self.update_mode
                else
                "Install UwUConverter for your user account. "
                "No system-wide Python installation is required."
            ),
            wraplength=640,
            justify="left",
        )
        subtitle.pack(
            anchor="w",
            pady=(
                6,
                18,
            ),
        )

        destination_frame = ttk.LabelFrame(
            outer,
            text="Installation",
            padding=12,
        )
        destination_frame.pack(
            fill="x",
        )

        ttk.Label(
            destination_frame,
            text=(
                "Destination: "
                + str(
                    app_directory()
                )
            ),
            wraplength=620,
        ).pack(
            anchor="w",
        )

        ttk.Label(
            destination_frame,
            text=(
                "Includes the application, batch converter, "
                "file-manager context menus, native browser bridge, "
                "and archive support."
            ),
            wraplength=620,
        ).pack(
            anchor="w",
            pady=(
                5,
                0,
            ),
        )

        options_frame = ttk.LabelFrame(
            outer,
            text="Options",
            padding=12,
        )
        options_frame.pack(
            fill="x",
            pady=(
                14,
                0,
            ),
        )

        ttk.Checkbutton(
            options_frame,
            text=(
                "Add the UwUConverter CLI command "
                "to ~/.local/bin"
            ),
            variable=self.cli_var,
        ).pack(
            anchor="w",
        )

        ttk.Checkbutton(
            options_frame,
            text=(
                "Check for UwUConverter updates "
                "automatically after login"
            ),
            variable=self.updater_var,
        ).pack(
            anchor="w",
            pady=(
                6,
                0,
            ),
        )

        if not self.update_mode:
            browser_frame = ttk.LabelFrame(
                outer,
                text="Browser extensions",
                padding=12,
            )
            browser_frame.pack(
                fill="x",
                pady=(
                    14,
                    0,
                ),
            )

            if self.detected_browsers:
                ttk.Label(
                    browser_frame,
                    text=(
                        "Select the detected browsers where "
                        "you want the UwUConverter extension:"
                    ),
                    wraplength=620,
                ).pack(
                    anchor="w",
                    pady=(
                        0,
                        6,
                    ),
                )

                for browser in (
                    self.detected_browsers
                ):
                    suffix = (
                        " (Flatpak)"
                        if browser[
                            "flatpak"
                        ]
                        else ""
                    )

                    variable = (
                        self.tk.BooleanVar(
                            value=True
                        )
                    )

                    self.browser_vars[
                        browser["id"]
                    ] = variable

                    ttk.Checkbutton(
                        browser_frame,
                        text=(
                            browser["name"]
                            + suffix
                        ),
                        variable=variable,
                    ).pack(
                        anchor="w",
                    )

                ttk.Label(
                    browser_frame,
                    text=(
                        "Until the extensions are published in browser "
                        "stores, Setup opens the extensions page and the "
                        "bundled extension folder for the selected browsers."
                    ),
                    wraplength=620,
                ).pack(
                    anchor="w",
                    pady=(
                        7,
                        0,
                    ),
                )
            else:
                ttk.Label(
                    browser_frame,
                    text=(
                        "No supported browsers were detected. "
                        "The native browser host will still be installed."
                    ),
                    wraplength=620,
                ).pack(
                    anchor="w",
                )

        self.progress = ttk.Progressbar(
            outer,
            mode="indeterminate",
        )

        self.status_label = ttk.Label(
            outer,
            text="Ready.",
            wraplength=620,
        )
        self.status_label.pack(
            anchor="w",
            pady=(
                16,
                4,
            ),
        )

        self.log_text = self.tk.Text(
            outer,
            height=7,
            wrap="word",
            state="disabled",
        )

        self.log_text.pack(
            fill="both",
            expand=True,
            pady=(
                4,
                12,
            ),
        )

        button_frame = ttk.Frame(
            outer
        )
        button_frame.pack(
            fill="x",
        )

        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_close,
        )
        self.cancel_button.pack(
            side="right",
        )

        self.install_button = ttk.Button(
            button_frame,
            text=(
                "Update"
                if self.update_mode
                else "Install"
            ),
            command=self.start_install,
        )
        self.install_button.pack(
            side="right",
            padx=(
                0,
                8,
            ),
        )

    def append_log(
        self,
        message,
    ):
        self.log_text.configure(
            state="normal",
        )

        self.log_text.insert(
            "end",
            message.rstrip()
            + "\n",
        )

        self.log_text.see(
            "end"
        )

        self.log_text.configure(
            state="disabled",
        )

    def start_install(self):
        if not self.install_script.is_file():
            from tkinter import messagebox

            messagebox.showerror(
                "UwUConverter Installer",
                (
                    "install.sh was not found beside "
                    "UwUConverterInstaller:\n\n"
                    + str(
                        self.install_script
                    )
                ),
                parent=self.root,
            )
            return

        self.install_button.configure(
            state="disabled",
        )
        self.cancel_button.configure(
            state="disabled",
        )

        self.progress.pack(
            fill="x",
            before=self.status_label,
            pady=(
                14,
                2,
            ),
        )
        self.progress.start(
            12
        )

        self.status_label.configure(
            text=(
                "Updating UwUConverter..."
                if self.update_mode
                else "Installing UwUConverter..."
            )
        )

        thread = threading.Thread(
            target=self.run_backend,
            daemon=True,
        )
        thread.start()

    def run_backend(self):
        command = [
            "bash",
            str(
                self.install_script
            ),
            "--from-gui",
            "--skip-browser-questions",
        ]

        if self.update_mode:
            command.append(
                "--update"
            )

        if not self.cli_var.get():
            command.append(
                "--no-cli"
            )

        if not self.updater_var.get():
            command.append(
                "--no-updater"
            )

        environment = (
            os.environ.copy()
        )

        # The GUI owns update cleanup so the backend does not remove the
        # directory containing the currently running installer.
        environment.pop(
            "UWUCONVERTER_UPDATE_TEMP",
            None,
        )

        try:
            process = subprocess.Popen(
                command,
                cwd=str(
                    self.package_dir
                ),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            assert (
                process.stdout
                is not None
            )

            for line in (
                process.stdout
            ):
                self.worker_queue.put(
                    (
                        "log",
                        line,
                    )
                )

            return_code = (
                process.wait()
            )

            self.worker_queue.put(
                (
                    "done",
                    return_code,
                )
            )

        except Exception as error:
            self.worker_queue.put(
                (
                    "error",
                    str(error),
                )
            )

    def poll_worker(self):
        try:
            while True:
                kind, value = (
                    self.worker_queue.get_nowait()
                )

                if kind == "log":
                    self.append_log(
                        value
                    )

                elif kind == "done":
                    self.finish_install(
                        value
                    )

                elif kind == "error":
                    self.fail_install(
                        value
                    )

        except queue.Empty:
            pass

        self.root.after(
            100,
            self.poll_worker,
        )

    def finish_install(
        self,
        return_code,
    ):
        self.install_finished = True

        self.progress.stop()
        self.progress.pack_forget()

        if return_code != 0:
            self.fail_install(
                "install.sh returned exit code "
                + str(return_code)
            )
            return

        self.install_succeeded = True

        if not self.update_mode:
            self.open_selected_browser_setup()

        self.status_label.configure(
            text=(
                "UwUConverter was updated successfully."
                if self.update_mode
                else "UwUConverter was installed successfully."
            )
        )

        self.install_button.configure(
            text="Finish",
            command=self.on_close,
            state="normal",
        )

        self.cancel_button.pack_forget()

    def fail_install(
        self,
        message,
    ):
        from tkinter import messagebox

        self.install_finished = True
        self.install_succeeded = False

        self.progress.stop()
        self.progress.pack_forget()

        self.status_label.configure(
            text="Installation failed."
        )

        self.append_log(
            message
        )

        self.install_button.configure(
            text=(
                "Retry"
                if not self.update_mode
                else "Retry update"
            ),
            command=self.start_install,
            state="normal",
        )

        self.cancel_button.configure(
            state="normal",
        )

        messagebox.showerror(
            "UwUConverter Installer",
            message,
            parent=self.root,
        )

    def open_selected_browser_setup(
        self,
    ):
        opened_families = set()
        installed_root = (
            app_directory()
        )

        for browser in (
            self.detected_browsers
        ):
            variable = (
                self.browser_vars.get(
                    browser["id"]
                )
            )

            if (
                variable is None
                or not variable.get()
            ):
                continue

            try:
                launch_browser(
                    browser,
                    browser["manager"],
                )
            except OSError as error:
                self.append_log(
                    (
                        "Could not open "
                        + browser["name"]
                        + ": "
                        + str(error)
                    )
                )

            family = browser[
                "family"
            ]

            if family in (
                opened_families
            ):
                continue

            folder = (
                installed_root
                / "browser-extension"
                / family
            )

            if folder.is_dir():
                open_folder(
                    folder
                )
                opened_families.add(
                    family
                )

    def schedule_cleanup(
        self,
    ):
        if (
            self.cleanup_scheduled
            or self.update_temp
            is None
        ):
            return

        self.cleanup_scheduled = True

        target = str(
            self.update_temp
        )

        subprocess.Popen(
            [
                "bash",
                "-c",
                (
                    "sleep 3; rm -rf -- "
                    + shlex.quote(
                        target
                    )
                ),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )

    def on_close(self):
        if (
            not self.install_finished
            and self.install_button[
                "state"
            ] == "disabled"
        ):
            return

        if (
            self.install_succeeded
            and self.update_mode
        ):
            self.schedule_cleanup()

        self.root.destroy()


def main(argv=None):
    args = build_parser().parse_args(
        argv
    )

    if not sys.platform.startswith(
        "linux"
    ):
        print(
            "UwUConverterInstaller is for Linux.",
            file=sys.stderr,
        )
        return 1

    if not (
        os.environ.get(
            "DISPLAY"
        )
        or os.environ.get(
            "WAYLAND_DISPLAY"
        )
    ):
        print(
            "No graphical desktop session was detected. "
            "Run ./install.sh for terminal installation.",
            file=sys.stderr,
        )
        return 2

    try:
        import tkinter as tk
    except Exception as error:
        print(
            "Tk could not be loaded: "
            + str(error),
            file=sys.stderr,
        )
        return 3

    root = tk.Tk()

    InstallerWindow(
        root,
        update_mode=args.update,
        update_temp=args.update_temp,
    )

    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
