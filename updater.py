import argparse
import hashlib
import json
import os
import pathlib
import platform
import shutil
import tarfile
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import webbrowser

from ssl_context import create_verified_ssl_context
from version import APP_VERSION, GITHUB_OWNER, GITHUB_REPO


CHECK_INTERVAL_SECONDS = 24 * 60 * 60
API_VERSION = "2026-03-10"

LATEST_RELEASE_API = (
    f"https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)

RELEASES_PAGE = (
    f"https://github.com/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}/releases"
)


def state_path():
    if os.name == "nt":
        root = pathlib.Path(
            os.environ.get(
                "LOCALAPPDATA",
                pathlib.Path.home(),
            )
        )
    else:
        root = (
            pathlib.Path.home()
            / ".local"
            / "state"
        )

    folder = root / "UwUConverter"
    folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    return folder / "updater_state.json"


def load_state():
    path = state_path()

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
    ):
        return {}


def save_state(state):
    path = state_path()
    temp = path.with_suffix(".tmp")

    temp.write_text(
        json.dumps(
            state,
            indent=2,
        ),
        encoding="utf-8",
    )

    os.replace(
        temp,
        path,
    )


def normalize_version(value):
    value = str(value).strip()

    if value.lower().startswith("v"):
        value = value[1:]

    value = value.split(
        "+",
        1,
    )[0]

    value = value.split(
        "-",
        1,
    )[0]

    pieces = []

    for part in value.split("."):
        digits = ""

        for char in part:
            if char.isdigit():
                digits += char
            else:
                break

        pieces.append(
            int(digits or "0")
        )

    while len(pieces) < 4:
        pieces.append(0)

    return tuple(pieces)


def is_newer_version(
    latest,
    current=APP_VERSION,
):
    return (
        normalize_version(latest)
        >
        normalize_version(current)
    )


def request_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": (
                f"UwUConverter/{APP_VERSION}"
            ),
            "X-GitHub-Api-Version": API_VERSION,
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=15,
        context=create_verified_ssl_context(),
    ) as response:
        return json.load(response)


def get_latest_release():
    return request_json(
        LATEST_RELEASE_API
    )


def select_windows_installer(release):
    assets = release.get(
        "assets",
        [],
    )

    exact_names = {
        "uwuconverter-setup.exe",
    }

    for asset in assets:
        name = str(
            asset.get(
                "name",
                "",
            )
        ).lower()

        if name in exact_names:
            return asset

    candidates = []

    for asset in assets:
        name = str(
            asset.get(
                "name",
                "",
            )
        ).lower()

        if (
            name.endswith(".exe")
            and "uwuconverter" in name
            and (
                "setup" in name
                or "installer" in name
            )
        ):
            candidates.append(
                asset
            )

    return (
        candidates[0]
        if candidates
        else None
    )


def select_linux_package(release):
    assets = release.get(
        "assets",
        [],
    )

    machine = platform.machine().lower()

    if machine in {"x86_64", "amd64"}:
        arch_tokens = (
            "x86_64",
            "x64",
            "amd64",
        )
    elif machine in {"aarch64", "arm64"}:
        arch_tokens = (
            "arm64",
            "aarch64",
        )
    else:
        arch_tokens = (
            machine,
        )

    exact_names = {
        f"uwuconverter-linux-{token}.tar.gz"
        for token in arch_tokens
    }

    for asset in assets:
        name = str(
            asset.get(
                "name",
                "",
            )
        ).lower()

        if name in exact_names:
            return asset

    candidates = []

    for asset in assets:
        name = str(
            asset.get(
                "name",
                "",
            )
        ).lower()

        if not (
            name.endswith(".tar.gz")
            or name.endswith(".tgz")
        ):
            continue

        if (
            "uwuconverter" not in name
            or "linux" not in name
        ):
            continue

        if any(
            token in name
            for token in arch_tokens
        ):
            candidates.append(
                asset
            )

    if candidates:
        return candidates[0]

    return None


def should_check(force=False):
    if force:
        return True

    state = load_state()
    last_check = float(
        state.get(
            "last_check",
            0,
        )
    )

    return (
        time.time() - last_check
        >= CHECK_INTERVAL_SECONDS
    )


def mark_checked(
    release=None,
):
    state = load_state()
    state["last_check"] = time.time()

    if release is not None:
        state["latest_tag"] = (
            release.get(
                "tag_name"
            )
        )

    save_state(
        state
    )


def check_for_update(force=False):
    if not should_check(
        force=force
    ):
        return None

    release = get_latest_release()

    mark_checked(
        release
    )

    tag = str(
        release.get(
            "tag_name",
            "",
        )
    )

    if not tag:
        return None

    if not is_newer_version(
        tag,
        APP_VERSION,
    ):
        return None

    return release


def download_asset(asset):
    url = asset.get(
        "browser_download_url"
    )

    if not url:
        raise RuntimeError(
            "Release asset has no download URL."
        )

    name = asset.get(
        "name"
    ) or "UwUConverter-Setup.exe"

    destination = (
        pathlib.Path(
            tempfile.gettempdir()
        )
        / name
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                f"UwUConverter/{APP_VERSION}"
            ),
        },
    )

    hasher = hashlib.sha256()

    with urllib.request.urlopen(
        request,
        timeout=60,
        context=create_verified_ssl_context(),
    ) as response:
        with destination.open(
            "wb"
        ) as output:
            while True:
                block = response.read(
                    1024 * 1024
                )

                if not block:
                    break

                output.write(
                    block
                )

                hasher.update(
                    block
                )

    if (
        not destination.is_file()
        or destination.stat().st_size <= 0
    ):
        raise RuntimeError(
            "Downloaded installer is empty."
        )

    digest = asset.get(
        "digest"
    )

    if (
        isinstance(digest, str)
        and digest.lower().startswith(
            "sha256:"
        )
    ):
        expected = digest.split(
            ":",
            1,
        )[1].lower()

        actual = hasher.hexdigest().lower()

        if actual != expected:
            destination.unlink(
                missing_ok=True
            )

            raise RuntimeError(
                "Downloaded installer SHA-256 "
                "does not match GitHub's asset digest."
            )

    return destination


def ask_to_update(
    latest_version,
):
    message = (
        "A new UwUConverter version is available.\n\n"
        f"Installed: {APP_VERSION}\n"
        f"Latest: {latest_version}\n\n"
        "Download and install it now?"
    )

    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()

        result = messagebox.askyesno(
            "UwUConverter Update",
            message,
        )

        root.destroy()
        return result

    except Exception:
        pass

    kdialog = shutil.which(
        "kdialog"
    )

    if kdialog:
        return (
            subprocess.run(
                [
                    kdialog,
                    "--title",
                    "UwUConverter Update",
                    "--yesno",
                    message,
                ],
                check=False,
            ).returncode
            == 0
        )

    zenity = shutil.which(
        "zenity"
    )

    if zenity:
        return (
            subprocess.run(
                [
                    zenity,
                    "--question",
                    "--title=UwUConverter Update",
                    "--text=" + message,
                ],
                check=False,
            ).returncode
            == 0
        )

    if sys.stdin.isatty():
        print(message)
        answer = input(
            "Update now? [y/N] "
        ).strip().lower()
        return answer in {
            "y",
            "yes",
        }

    return False



def show_info(
    title,
    message,
):
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()

        messagebox.showinfo(
            title,
            message,
        )

        root.destroy()

    except Exception:
        pass


def show_error(
    message,
):
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()

        messagebox.showerror(
            "UwUConverter Update Failed",
            message,
        )

        root.destroy()

    except Exception:
        pass


def extract_linux_package(package_path):
    package = pathlib.Path(
        package_path
    ).resolve()

    if not package.is_file():
        raise FileNotFoundError(
            f"Linux update package does not exist: {package}"
        )

    destination = pathlib.Path(
        tempfile.mkdtemp(
            prefix="UwUConverter-update-",
        )
    )

    with tarfile.open(
        package,
        "r:*",
    ) as archive:
        try:
            archive.extractall(
                destination,
                filter="data",
            )
        except TypeError:
            # Python versions before tarfile's extraction filters need
            # an explicit path traversal check.
            root = destination.resolve()

            for member in archive.getmembers():
                if member.issym() or member.islnk():
                    raise RuntimeError(
                        "Unsafe link in Linux update archive: "
                        + member.name
                    )

                target = (
                    destination
                    / member.name
                ).resolve()

                try:
                    target.relative_to(
                        root
                    )
                except ValueError as error:
                    raise RuntimeError(
                        "Unsafe path in Linux update archive: "
                        + member.name
                    ) from error

            archive.extractall(
                destination
            )

    installers = sorted(
        destination.rglob(
            "install.sh"
        ),
        key=lambda item: len(
            item.parts
        ),
    )

    if not installers:
        shutil.rmtree(
            destination,
            ignore_errors=True,
        )

        raise RuntimeError(
            "Linux update package does not contain install.sh."
        )

    install_script = installers[0]

    try:
        install_script.chmod(
            install_script.stat().st_mode
            | 0o111
        )
    except OSError:
        pass

    return destination, install_script


def launch_linux_installer(package_path):
    extraction_root, install_script = (
        extract_linux_package(
            package_path
        )
    )

    environment = os.environ.copy()
    environment[
        "UWUCONVERTER_UPDATE_TEMP"
    ] = str(
        extraction_root
    )

    subprocess.Popen(
        [
            "bash",
            str(install_script),
            "--update",
        ],
        cwd=str(
            install_script.parent
        ),
        env=environment,
        start_new_session=True,
        close_fds=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def launch_windows_installer(
    installer,
):
    arguments = [
        str(installer),
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/CLOSEAPPLICATIONS",
    ]

    subprocess.Popen(
        arguments,
        cwd=str(
            installer.parent
        ),
        close_fds=True,
    )


def install_release(
    release,
    assume_yes=False,
):
    latest = release.get(
        "tag_name",
        "unknown",
    )

    if (
        not assume_yes
        and not ask_to_update(
            latest
        )
    ):
        return False

    if os.name == "nt":
        asset = select_windows_installer(
            release
        )

        if asset is None:
            raise RuntimeError(
                "The latest GitHub release does not contain "
                "a UwUConverter Windows installer asset."
            )

        installer = download_asset(
            asset
        )

        launch_windows_installer(
            installer
        )

        return True

    if sys.platform.startswith(
        "linux"
    ):
        asset = select_linux_package(
            release
        )

        if asset is None:
            raise RuntimeError(
                "The latest GitHub release does not contain "
                "a UwUConverter Linux package for this architecture."
            )

        package = download_asset(
            asset
        )

        launch_linux_installer(
            package
        )

        return True

    raise RuntimeError(
        "Automatic installation is not supported on "
        + sys.platform
        + "."
    )



def run_update(
    force=False,
    check_only=False,
    assume_yes=False,
    quiet=False,
):
    try:
        release = check_for_update(
            force=force
        )

        if release is None:
            if not quiet:
                print(
                    "UwUConverter is up to date."
                )

            return 0

        latest = release.get(
            "tag_name",
            "unknown",
        )

        if check_only:
            if not quiet:
                print(
                    f"Update available: "
                    f"{APP_VERSION} -> {latest}"
                )

            return 10

        installed = install_release(
            release,
            assume_yes=assume_yes,
        )

        if installed:
            if not quiet:
                print(
                    f"Installing UwUConverter {latest}..."
                )

            return 0

        if not quiet:
            print(
                "Update cancelled."
            )

        return 0

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        RuntimeError,
        ValueError,
    ) as error:
        if quiet:
            return 1

        print(
            "Update failed: "
            + str(error),
            file=sys.stderr,
        )

        return 1


def automatic_check():
    # Login/startup checks should never interrupt normal application
    # use because of a network failure.
    try:
        release = check_for_update(
            force=False
        )

        if release is None:
            return 0

        install_release(
            release,
            assume_yes=False,
        )

        return 0

    except Exception:
        return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="UwUConverterUpdater",
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Run the normal once-per-day automatic check.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore the 24-hour update-check cache.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check for an update without installing it.",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Install without asking for confirmation.",
    )

    return parser


def main(argv=None):
    args = build_parser().parse_args(
        argv
    )

    if args.auto:
        return automatic_check()

    return run_update(
        force=args.force,
        check_only=args.check_only,
        assume_yes=args.yes,
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
