import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time


# Fill these after the extension is published. If you feel like paying. which your broke ass wont
CHROMIUM_STORE_URL = ""
FIREFOX_AMO_URL = "https://addons.mozilla.org/en-US/firefox/addon/uwuconverter-browser/"
OPERA_STORE_URL = ""


BROWSERS = [
    {
        "id": "chrome",
        "name": "Google Chrome",
        "family": "chromium",
        "manager_url": "chrome://extensions",
        "linux_commands": ["google-chrome", "google-chrome-stable"],
        "flatpak_ids": ["com.google.Chrome"],
    },
    {
        "id": "chromium",
        "name": "Chromium",
        "family": "chromium",
        "manager_url": "chrome://extensions",
        "linux_commands": ["chromium", "chromium-browser"],
        "flatpak_ids": ["org.chromium.Chromium"],
    },
    {
        "id": "edge",
        "name": "Microsoft Edge",
        "family": "chromium",
        "manager_url": "edge://extensions",
        "linux_commands": [
            "microsoft-edge",
            "microsoft-edge-stable",
            "microsoft-edge-beta",
            "microsoft-edge-dev",
        ],
        "flatpak_ids": ["com.microsoft.Edge"],
    },
    {
        "id": "opera",
        "name": "Opera",
        "family": "chromium",
        "manager_url": "opera://extensions",
        "linux_commands": ["opera", "opera-stable", "opera-beta", "opera-developer"],
        "flatpak_ids": ["com.opera.Opera"],
    },
    {
        "id": "opera-gx",
        "name": "Opera GX",
        "family": "chromium",
        "manager_url": "opera://extensions",
        "linux_commands": ["opera-gx", "opera-gx-stable"],
        "flatpak_ids": ["com.opera.opera-gx"],
    },
    {
        "id": "brave",
        "name": "Brave",
        "family": "chromium",
        "manager_url": "brave://extensions",
        "linux_commands": ["brave-browser", "brave-browser-stable", "brave"],
        "flatpak_ids": ["com.brave.Browser"],
    },
    {
        "id": "vivaldi",
        "name": "Vivaldi",
        "family": "chromium",
        "manager_url": "vivaldi://extensions",
        "linux_commands": ["vivaldi", "vivaldi-stable", "vivaldi-snapshot"],
        "flatpak_ids": ["com.vivaldi.Vivaldi"],
    },
    {
        "id": "firefox",
        "name": "Firefox",
        "family": "firefox",
        "manager_url": "about:debugging#/runtime/this-firefox",
        "linux_commands": ["firefox", "firefox-esr"],
        "flatpak_ids": ["org.mozilla.firefox"],
    },
]


def application_directory():
    if getattr(sys, "frozen", False):
        return pathlib.Path(sys.executable).resolve().parent
    return pathlib.Path(__file__).resolve().parent


def state_path():
    if os.name == "nt":
        base = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home()))
    else:
        base = pathlib.Path(
            os.environ.get("XDG_STATE_HOME", pathlib.Path.home() / ".local/state")
        )
    folder = base / "UwUConverter"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "browser_setup_state.json"


def load_state():
    try:
        return json.loads(state_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_offered_browsers(browser_ids):
    state = load_state()
    offered = set(state.get("offered_browsers", []))
    offered.update(browser_ids)
    state["offered_browsers"] = sorted(offered)
    state["last_browser_setup"] = time.time()
    path = state_path()
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.replace(temp, path)


def extension_folder(family):
    folder_name = "firefox" if family == "firefox" else "chromium"
    candidates = [
        application_directory() / "browser-extension" / folder_name,
        application_directory() / "browser_extension" / folder_name,
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "manifest.json").is_file():
            return candidate.resolve()
    return None


def _windows_browser_candidates(browser_id):
    local = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home()))
    pf = pathlib.Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
    pfx86 = pathlib.Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))

    mapping = {
        "chrome": [
            pf / "Google/Chrome/Application/chrome.exe",
            pfx86 / "Google/Chrome/Application/chrome.exe",
            local / "Google/Chrome/Application/chrome.exe",
        ],
        "chromium": [
            pf / "Chromium/Application/chrome.exe",
            pfx86 / "Chromium/Application/chrome.exe",
            local / "Chromium/Application/chrome.exe",
        ],
        "edge": [
            pf / "Microsoft/Edge/Application/msedge.exe",
            pfx86 / "Microsoft/Edge/Application/msedge.exe",
            local / "Microsoft/Edge/Application/msedge.exe",
        ],
        "opera": [
            local / "Programs/Opera/opera.exe",
            local / "Programs/Opera/launcher.exe",
            pf / "Opera/opera.exe",
            pfx86 / "Opera/opera.exe",
        ],
        "opera-gx": [
            local / "Programs/Opera GX/opera.exe",
            local / "Programs/Opera GX/launcher.exe",
            pf / "Opera GX/opera.exe",
            pfx86 / "Opera GX/opera.exe",
        ],
        "brave": [
            pf / "BraveSoftware/Brave-Browser/Application/brave.exe",
            pfx86 / "BraveSoftware/Brave-Browser/Application/brave.exe",
            local / "BraveSoftware/Brave-Browser/Application/brave.exe",
        ],
        "vivaldi": [
            local / "Vivaldi/Application/vivaldi.exe",
            pf / "Vivaldi/Application/vivaldi.exe",
            pfx86 / "Vivaldi/Application/vivaldi.exe",
        ],
        "firefox": [
            pf / "Mozilla Firefox/firefox.exe",
            pfx86 / "Mozilla Firefox/firefox.exe",
            local / "Mozilla Firefox/firefox.exe",
        ],
    }

    candidates = list(mapping.get(browser_id, []))
    if browser_id in {"opera", "opera-gx"}:
        parent_name = "Opera GX" if browser_id == "opera-gx" else "Opera"
        install_root = local / "Programs" / parent_name
        if install_root.is_dir():
            candidates.extend(install_root.glob("*/opera.exe"))
    return candidates


def _flatpak_installed(app_id):
    flatpak = shutil.which("flatpak")
    if not flatpak:
        return False
    try:
        result = subprocess.run(
            [flatpak, "info", app_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=4,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def detect_browsers():
    detected = []
    for definition in BROWSERS:
        item = dict(definition)
        command = None
        sandboxed = False

        if os.name == "nt":
            for candidate in _windows_browser_candidates(definition["id"]):
                candidate = pathlib.Path(candidate)
                if candidate.is_file():
                    command = [str(candidate.resolve())]
                    break
        elif sys.platform.startswith("linux"):
            for name in definition["linux_commands"]:
                executable = shutil.which(name)
                if executable:
                    command = [executable]
                    break
            if command is None:
                for app_id in definition["flatpak_ids"]:
                    if _flatpak_installed(app_id):
                        command = [shutil.which("flatpak") or "flatpak", "run", app_id]
                        sandboxed = True
                        break

        if command is None:
            continue
        item["command"] = command
        item["sandboxed"] = sandboxed
        detected.append(item)
    return detected


def launch_browser(browser, url):
    command = list(browser["command"]) + [url]
    kwargs = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name != "nt":
        kwargs["start_new_session"] = True
    subprocess.Popen(command, **kwargs)


def open_folder(path):
    path = pathlib.Path(path).resolve()
    if os.name == "nt":
        os.startfile(str(path))
        return
    opener = shutil.which("xdg-open")
    if opener:
        subprocess.Popen(
            [opener, str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
        return
    raise RuntimeError("Could not find xdg-open.")


def store_url_for(browser):
    if browser["family"] == "firefox":
        return FIREFOX_AMO_URL.strip()
    if browser["id"] in {"opera", "opera-gx"} and OPERA_STORE_URL.strip():
        return OPERA_STORE_URL.strip()
    return CHROMIUM_STORE_URL.strip()


def install_for_browser(browser, show_info, show_error):
    store_url = store_url_for(browser)
    if store_url:
        try:
            launch_browser(browser, store_url)
        except OSError as error:
            show_error(f"Could not launch {browser['name']}:\n\n{error}")
        return

    family = browser["family"]
    folder = extension_folder(family)
    if folder is None:
        show_error(
            "The bundled browser extension folder was not found.\n\n"
            "Reinstall UwUConverter or use a build that includes browser-extension/."
        )
        return

    try:
        launch_browser(browser, browser["manager_url"])
        open_folder(folder)
    except OSError as error:
        show_error(f"Could not launch the browser installation helper:\n\n{error}")
        return

    if family == "firefox":
        instructions = (
            "Firefox development install\n\n"
            "1. Firefox opened about:debugging.\n"
            "2. Choose 'Load Temporary Add-on'.\n"
            "3. Select manifest.json in the folder that UwUConverter opened.\n\n"
            "A permanent normal Firefox install requires the add-on to be signed/published. "
            "Once an AMO URL is configured, this button will open the normal install page instead."
        )
    else:
        instructions = (
            f"{browser['name']} development install\n\n"
            "1. Enable Developer mode on the extensions page.\n"
            "2. Choose 'Load unpacked'.\n"
            "3. Select the Chromium extension folder that UwUConverter opened.\n\n"
            "Once the extension has a store listing, this button can open the normal one-click "
            "store installation page instead."
        )

    if browser.get("sandboxed"):
        instructions += (
            "\n\nThis browser was detected as a Flatpak. The extension can be installed normally, "
            "but Native Messaging may require additional sandbox permission depending on the browser package."
        )
    show_info(instructions)


def run_gui(detected):
    import tkinter as tk
    from tkinter import messagebox, ttk

    root = tk.Tk()
    root.title("UwUConverter Browser Setup")
    root.minsize(620, 300)

    try:
        icon_path = application_directory() / "UwUConverter.ico"
        if icon_path.is_file():
            root.iconbitmap(default=str(icon_path))
    except Exception:
        pass

    outer = ttk.Frame(root, padding=18)
    outer.pack(fill="both", expand=True)

    ttk.Label(
        outer,
        text="Install UwUConverter browser integration",
        font=("TkDefaultFont", 13, "bold"),
    ).pack(anchor="w")

    ttk.Label(
        outer,
        text=(
            "The native UwUConverter bridge is already installed. "
            "Choose which detected browsers should get the extension."
        ),
        wraplength=580,
        justify="left",
    ).pack(anchor="w", pady=(6, 14))

    list_frame = ttk.Frame(outer)
    list_frame.pack(fill="x")

    def info(message):
        messagebox.showinfo("UwUConverter Browser Setup", message, parent=root)

    def error(message):
        messagebox.showerror("UwUConverter Browser Setup", message, parent=root)

    for browser in detected:
        row = ttk.Frame(list_frame)
        row.pack(fill="x", pady=3)
        status = "Detected" + (" (Flatpak)" if browser.get("sandboxed") else "")
        ttk.Label(row, text=f"{browser['name']} - {status}").pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(
            row,
            text="Install extension",
            command=lambda current=browser: install_for_browser(current, info, error),
        ).pack(side="right")

    if not detected:
        ttk.Label(list_frame, text="No supported desktop browsers were detected.").pack(anchor="w")

    if not (CHROMIUM_STORE_URL.strip() or FIREFOX_AMO_URL.strip() or OPERA_STORE_URL.strip()):
        ttk.Label(
            outer,
            text=(
                "Development build: no browser-store URLs are configured yet, so the buttons "
                "open the browser's extension manager and UwUConverter's bundled unpacked extension folder."
            ),
            wraplength=580,
            justify="left",
        ).pack(anchor="w", pady=(16, 8))

    ttk.Button(outer, text="Done", command=root.destroy).pack(anchor="e", pady=(8, 0))
    root.mainloop()


def build_parser():
    parser = argparse.ArgumentParser(prog="UwUConverterBrowserSetup")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Show only when a newly detected browser has not been offered browser setup before.",
    )
    parser.add_argument("--force", action="store_true", help="Always open browser setup.")
    parser.add_argument("--list", action="store_true", help="Print detected browsers and exit.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    detected = detect_browsers()

    if args.list:
        for browser in detected:
            print(browser["id"] + "\t" + browser["name"])
        return 0

    browser_ids = {browser["id"] for browser in detected}
    if args.auto and not args.force:
        if not browser_ids:
            return 0
        offered = set(load_state().get("offered_browsers", []))
        if browser_ids.issubset(offered):
            return 0

    if sys.platform.startswith("linux") and not (
        os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    ):
        return 0

    try:
        run_gui(detected)
    except Exception as error:
        if not args.auto:
            print("Browser setup failed: " + str(error), file=sys.stderr)
            return 1
        return 0

    if browser_ids:
        save_offered_browsers(browser_ids)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
