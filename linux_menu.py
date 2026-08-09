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

DOLPHIN_OLD_PATTERNS = [
    "uwuconverter-*.desktop",
    "UwUConverter-*.desktop",
]

OLD_SCRIPT_NAMES = {
    "Batch Convert With UwUConverter",
}


# KDE/Dolphin service menus match MIME types, not filename extensions.
# Keep this intentionally simple and explicit for the formats supported
# by UwUConverter.
MIME_TYPES = {
    ".mp4": "video/mp4",
    ".mkv": "video/x-matroska",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".webm": "video/webm",

    ".mp3": "audio/mpeg",
    ".wav": "audio/x-wav",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".opus": "audio/ogg",

    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".raw": "image/x-dcraw",

    ".pdf": "application/pdf",
    ".docx": (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ),
    ".odt": "application/vnd.oasis.opendocument.text",
    ".txt": "text/plain",

    ".xlsx": (
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    ),
    ".xls": "application/vnd.ms-excel",
    ".xlsb": "application/vnd.ms-excel.sheet.binary.macroEnabled.12",
    ".xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".csv": "text/csv",
    ".tsv": "text/tab-separated-values",

    ".obj": "model/obj",
    ".stl": "model/stl",
    ".ply": "application/x-ply",
    ".glb": "model/gltf-binary",
}


def CreateExtensions(file_types):
    cleanup_linux_integrations()

    # Nautilus/Nemo/Caja currently get the folder batch launcher.
    for manager, root in SCRIPT_FOLDERS.items():
        app_folder = root / APP_FOLDER_NAME
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
    create_dolphin_file_menus(file_types)

    print(
        "Installed Dolphin UwUConverter menus: "
        + str(DOLPHIN_FOLDER)
    )


def RemoveExtensions(file_types=None):
    removed = cleanup_linux_integrations()

    if removed:
        print(
            "Removed UwUConverter Linux integrations:"
        )

        for path in removed:
            print(path)
    else:
        print(
            "No UwUConverter Linux integrations were found."
        )


def cleanup_linux_integrations():
    removed = []

    for root in SCRIPT_FOLDERS.values():
        app_folder = root / APP_FOLDER_NAME

        if app_folder.exists():
            shutil.rmtree(app_folder)
            removed.append(str(app_folder))

        for old_name in OLD_SCRIPT_NAMES:
            old_path = root / old_name

            if old_path.exists():
                if old_path.is_dir():
                    shutil.rmtree(old_path)
                else:
                    old_path.unlink()

                removed.append(str(old_path))

    if DOLPHIN_FOLDER.exists():
        found = set()

        for pattern in DOLPHIN_OLD_PATTERNS:
            for path in DOLPHIN_FOLDER.glob(pattern):
                found.add(path)

        for path in sorted(found):
            if path.is_file() or path.is_symlink():
                path.unlink()
                removed.append(str(path))
            elif path.is_dir():
                shutil.rmtree(path)
                removed.append(str(path))

    return removed


def create_dolphin_batch_gui_menu():
    DOLPHIN_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

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


def create_dolphin_file_menus(file_types):
    DOLPHIN_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    # Dolphin matches service menus by MIME type. Several extensions
    # can share one MIME type, so creating one .desktop file per
    # extension can duplicate the same submenu.
    grouped = {}

    for extension, conversions in file_types.items():
        mime_type = MIME_TYPES.get(
            extension.lower()
        )

        if not mime_type or not conversions:
            continue

        actions = flatten_conversions(
            conversions
        )

        if not actions:
            continue

        grouped.setdefault(
            mime_type,
            []
        )

        existing = set(
            grouped[mime_type]
        )

        for action in actions:
            if action not in existing:
                grouped[mime_type].append(
                    action
                )
                existing.add(action)

    for mime_type, actions in grouped.items():
        safe_mime = (
            mime_type.lower()
            .replace("/", "-")
            .replace("+", "_")
            .replace(".", "_")
        )

        path = (
            DOLPHIN_FOLDER
            / f"uwuconverter-file-{safe_mime}.desktop"
        )

        action_ids = [
            f"uwu{index:02d}"
            for index in range(
                1,
                len(actions) + 1
            )
        ]

        lines = [
            "[Desktop Entry]",
            "Type=Service",
            "MimeType=" + mime_type + ";",
            "Actions=" + ";".join(action_ids) + ";",
            "X-KDE-Submenu=Convert With UwUConverter ^-^",
            "X-KDE-Priority=TopLevel",
            "",
        ]

        for action_id, (
            label,
            convert_type
        ) in zip(action_ids, actions):
            command = " ".join(
                shlex.quote(part)
                for part in single_file_command(
                    convert_type
                )
            )

            lines.extend(
                [
                    f"[Desktop Action {action_id}]",
                    "Name=" + label,
                    "Icon=document-convert",
                    "Exec=" + command + " %f",
                    "",
                ]
            )

        path.write_text(
            "\n".join(lines),
            encoding="utf-8"
        )

        make_executable(path)


def flatten_conversions(items, prefix=""):
    result = []

    for _, label, action in items:
        if isinstance(action, list):
            nested_prefix = (
                label
                if not prefix
                else prefix + " - " + label
            )

            result.extend(
                flatten_conversions(
                    action,
                    nested_prefix
                )
            )
            continue

        display_label = (
            label
            if not prefix
            else prefix + " - " + label
        )

        result.append(
            (
                display_label,
                action
            )
        )

    return result


def single_file_command(convert_type):
    if getattr(sys, "frozen", False):
        return [
            sys.executable,
            "%f",
            convert_type,
        ]

    converter = (
        pathlib.Path(__file__)
        .resolve()
        .parent
        / "Converter.py"
    )

    return [
        sys.executable,
        str(converter),
        "%f",
        convert_type,
    ]


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
