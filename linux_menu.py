import pathlib
import shlex
import shutil
import stat
import sys


APP_FOLDER_NAME = "UwUConverter"

SCRIPT_FOLDERS = {
    "Nautilus": pathlib.Path.home()
    / ".local/share/nautilus/scripts",
    "Nemo": pathlib.Path.home()
    / ".local/share/nemo/scripts",
    "Caja": pathlib.Path.home()
    / ".config/caja/scripts",
}

DOLPHIN_FOLDER = (
    pathlib.Path.home()
    / ".local/share/kio/servicemenus"
)


def CreateExtensions(file_types):
    for manager, root in SCRIPT_FOLDERS.items():
        app_folder = root / APP_FOLDER_NAME

        if app_folder.exists():
            shutil.rmtree(app_folder)

        app_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        launcher = app_folder / (
            "Batch Convert With UwUConverter"
        )

        launcher.write_text(
            build_folder_gui_script(),
            encoding="utf-8"
        )

        make_executable(launcher)

        print(
            f"Installed {manager} batch GUI launcher: "
            f"{launcher}"
        )

    create_dolphin_batch_gui_menu()

    print(
        "Installed Dolphin batch GUI menu: "
        + str(DOLPHIN_FOLDER)
    )


def RemoveExtensions(file_types=None):
    for root in SCRIPT_FOLDERS.values():
        app_folder = root / APP_FOLDER_NAME

        if app_folder.exists():
            shutil.rmtree(app_folder)

    if DOLPHIN_FOLDER.exists():
        for path in DOLPHIN_FOLDER.glob(
            "uwuconverter-batch-gui*.desktop"
        ):
            path.unlink()

    print(
        "Removed UwUConverter Linux batch GUI menus."
    )


def create_dolphin_batch_gui_menu():
    DOLPHIN_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    for old in DOLPHIN_FOLDER.glob(
        "uwuconverter-batch-gui*.desktop"
    ):
        old.unlink()

    path = (
        DOLPHIN_FOLDER
        / "uwuconverter-batch-gui.desktop"
    )

    command = " ".join(
        shlex.quote(part)
        for part in batch_gui_command()
    )

    content = "\n".join(
        [
            "[Desktop Entry]",
            "Type=Service",
            "MimeType=inode/directory;",
            "Actions=uwuBatchGui;",
            "X-KDE-Priority=TopLevel",
            "",
            "[Desktop Action uwuBatchGui]",
            "Name=Batch Convert With UwUConverter",
            "Icon=document-convert",
            "Exec=" + command + " %f",
            "",
        ]
    )

    path.write_text(
        content,
        encoding="utf-8"
    )

    make_executable(path)


def build_folder_gui_script():
    command = " ".join(
        shlex.quote(part)
        for part in batch_gui_command()
    )

    return (
        "#!/usr/bin/env bash\n"
        "set -u\n"
        "for folder_path in \"$@\"; do\n"
        "    if [ -d \"$folder_path\" ]; then\n"
        f"        {command} \"$folder_path\" "
        ">/dev/null 2>&1 &\n"
        "    fi\n"
        "done\n"
    )


def batch_gui_command():
    if getattr(sys, "frozen", False):
        executable_folder = pathlib.Path(
            sys.executable
        ).resolve().parent

        batch_executable = (
            executable_folder
            / "UwUConverterBatch"
        )

        if batch_executable.is_file():
            return [str(batch_executable)]

        # Fallback: the main executable can still open the GUI.
        return [
            sys.executable,
            "__BATCH_GUI__",
        ]

    launcher = (
        pathlib.Path(__file__)
        .resolve()
        .parent
        / "BatchLauncher.py"
    )

    return [
        sys.executable,
        str(launcher),
    ]


def make_executable(path):
    path.chmod(
        path.stat().st_mode
        | stat.S_IXUSR
        | stat.S_IXGRP
        | stat.S_IXOTH
    )
