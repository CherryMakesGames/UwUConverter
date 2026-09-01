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



DOLPHIN_FILE_CATEGORIES = {
    "video": [
        ".mp4",
        ".mkv",
        ".mov",
        ".avi",
        ".webm",
    ],
    "audio": [
        ".mp3",
        ".wav",
        ".ogg",
        ".flac",
        ".opus",
    ],
    "image": [
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".ico",
        ".tif",
        ".tiff",
        ".raw",
    ],
    "document": [
        ".pdf",
        ".docx",
        ".odt",
        ".txt",
    ],
    "spreadsheet": [
        ".xlsx",
        ".xls",
        ".xlsb",
        ".xlsm",
        ".ods",
        ".csv",
        ".tsv",
    ],
    "model": [
        ".obj",
        ".stl",
        ".ply",
        ".glb",
    ],
}


ARCHIVE_MIME_TYPES = [
    "application/x-7z-compressed",
    "application/zip",
    "application/vnd.rar",
    "application/x-rar",
    "application/x-tar",
    "application/gzip",
    "application/x-gzip",
    "application/x-bzip2",
    "application/x-xz",
    "application/x-lzma",
    "application/vnd.ms-cab-compressed",
    "application/x-iso9660-image",
    "application/x-arj",
    "application/x-lzh-compressed",
    "application/x-xar",
]

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

        zip_launcher = app_folder / (
            "Compress Selection to ZIP With UwUConverter"
        )

        zip_launcher.write_text(
            build_zip_selection_script(),
            encoding="utf-8"
        )

        make_executable(
            zip_launcher
        )

        print(
            f"Installed {manager} batch GUI launcher: "
            f"{launcher}"
        )

    create_dolphin_batch_gui_menu()
    create_dolphin_file_menus(file_types)
    create_dolphin_archive_menu()
    create_dolphin_zip_selection_menu()

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

    # Use one universal service menu for every supported conversion MIME
    # type. This keeps the menu visible for mixed selections such as:
    # PNG + JPG + MP4, or PDF + XLSX + WEBP.
    #
    # UwUConverter receives the whole selection and skips files for which
    # the chosen action is not valid.
    mime_types = []
    actions = []
    seen_actions = set()

    category_labels = {
        "video": "Video",
        "audio": "Audio",
        "image": "Image",
        "document": "Document",
        "spreadsheet": "Spreadsheet",
        "model": "3D Model",
    }

    for category, extensions in (
        DOLPHIN_FILE_CATEGORIES.items()
    ):
        category_label = category_labels.get(
            category,
            category.title()
        )

        for extension in extensions:
            mime_type = MIME_TYPES.get(
                extension
            )

            if (
                mime_type
                and mime_type not in mime_types
            ):
                mime_types.append(
                    mime_type
                )

            conversions = file_types.get(
                extension,
                []
            )

            for label, convert_type in (
                flatten_conversions(
                    conversions
                )
            ):
                action_key = (
                    category,
                    str(convert_type).lower(),
                )

                if action_key in seen_actions:
                    continue

                seen_actions.add(
                    action_key
                )

                # The same visible conversion names can exist in multiple
                # categories, for example "Convert To PDF" for images,
                # documents and spreadsheets. Prefixing the category keeps
                # each action unambiguous in one universal menu.
                actions.append(
                    (
                        category_label
                        + " - "
                        + label,
                        convert_type,
                    )
                )

    if (
        not mime_types
        or not actions
    ):
        return

    path = (
        DOLPHIN_FOLDER
        / "uwuconverter-files-universal.desktop"
    )

    action_ids = [
        f"uwu{index:03d}"
        for index in range(
            1,
            len(actions) + 1
        )
    ]

    lines = [
        "[Desktop Entry]",
        "Type=Service",
        "MimeType="
        + ";".join(mime_types)
        + ";",
        "Actions="
        + ";".join(action_ids)
        + ";",
        "X-KDE-Submenu="
        "Convert With UwUConverter ^-^",
        "X-KDE-Priority=TopLevel",
        "",
    ]

    for action_id, (
        label,
        convert_type
    ) in zip(
        action_ids,
        actions
    ):
        command = " ".join(
            shlex.quote(part)
            for part in multi_file_command(
                convert_type
            )
        )

        lines.extend(
            [
                f"[Desktop Action {action_id}]",
                "Name=" + label,
                "Icon=document-convert",
                "Exec=" + command + " %F",
                "",
            ]
        )

    path.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    make_executable(path)



def create_dolphin_zip_selection_menu():
    DOLPHIN_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    path = (
        DOLPHIN_FOLDER
        / "uwuconverter-compress-selection-zip.desktop"
    )

    command = " ".join(
        shlex.quote(part)
        for part in multi_file_command(
            "ARCHIVE_CREATE_ZIP_PROMPT"
        )
    )

    content = "\n".join(
        [
            "[Desktop Entry]",
            "Type=Service",
            "MimeType=application/octet-stream;inode/directory;",
            "Actions=uwuCompressSelectionZip;",
            "X-KDE-Priority=TopLevel",
            "",
            "[Desktop Action uwuCompressSelectionZip]",
            "Name=Compress Selection to ZIP With UwUConverter",
            "Icon=archive-insert",
            "Exec=" + command + " %F",
            "",
        ]
    )

    path.write_text(
        content,
        encoding="utf-8"
    )

    make_executable(
        path
    )


def create_dolphin_archive_menu():
    DOLPHIN_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    path = (
        DOLPHIN_FOLDER
        / "uwuconverter-archive-extract.desktop"
    )

    mime_line = ";".join(
        ARCHIVE_MIME_TYPES
    ) + ";"

    actions = [
        (
            "uwuExtractHere",
            "Extract Here",
            "ARCHIVE_EXTRACT_HERE",
        ),
        (
            "uwuExtractFolder",
            "Extract to Archive-Named Folder",
            "ARCHIVE_EXTRACT_FOLDER",
        ),
        (
            "uwuExtractHereDelete",
            "Extract Here and Delete Archive",
            "ARCHIVE_EXTRACT_HERE_DELETE",
        ),
        (
            "uwuExtractFolderDelete",
            "Extract to Archive-Named Folder and Delete Archive",
            "ARCHIVE_EXTRACT_FOLDER_DELETE",
        ),
    ]

    lines = [
        "[Desktop Entry]",
        "Type=Service",
        "MimeType=" + mime_line,
        "Actions="
        + ";".join(
            action_id
            for action_id, _, _ in actions
        )
        + ";",
        "X-KDE-Submenu="
        "Extract With UwUConverter ^-^",
        "X-KDE-Priority=TopLevel",
        "",
    ]

    for action_id, label, action in actions:
        command = " ".join(
            shlex.quote(part)
            for part in multi_file_command(
                action
            )
        )

        lines.extend(
            [
                f"[Desktop Action {action_id}]",
                "Name=" + label,
                "Icon=archive-extract",
                "Exec=" + command + " %F",
                "",
            ]
        )

    path.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    make_executable(path)



def archive_cli_command(arguments):
    if getattr(sys, "frozen", False):
        installed_cli = (
            pathlib.Path.home()
            / ".local/bin/UwUConverter"
        )

        if installed_cli.is_file():
            return [
                str(installed_cli),
                *arguments,
            ]

        executable_folder = pathlib.Path(
            sys.executable
        ).resolve().parent

        for name in (
            "UwUConverterCLI",
            "UwUConverter",
        ):
            candidate = executable_folder / name

            if (
                candidate.is_file()
                and candidate.resolve()
                != pathlib.Path(
                    sys.executable
                ).resolve()
            ):
                return [
                    str(candidate),
                    *arguments,
                ]

        raise FileNotFoundError(
            "UwUConverter CLI was not found. "
            "Install the CLI before creating archive menus."
        )

    cli_script = (
        pathlib.Path(__file__)
        .resolve()
        .parent
        / "cli.py"
    )

    return [
        sys.executable,
        str(cli_script),
        *arguments,
    ]


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


def multi_file_command(convert_type):
    if getattr(sys, "frozen", False):
        return [
            sys.executable,
            "__MULTI__",
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
        "__MULTI__",
        convert_type,
    ]



def build_zip_selection_script():
    command = " ".join(
        shlex.quote(part)
        for part in multi_file_command(
            "ARCHIVE_CREATE_ZIP_PROMPT"
        )
    )

    return (
        "#!/usr/bin/env bash\n"
        "set -u\n"
        "paths=()\n"
        "\n"
        "if [ \"$#\" -gt 0 ]; then\n"
        "    paths=(\"$@\")\n"
        "else\n"
        "    selected=\"${NAUTILUS_SCRIPT_SELECTED_FILE_PATHS:-}\"\n"
        "    if [ -z \"$selected\" ]; then\n"
        "        selected=\"${NEMO_SCRIPT_SELECTED_FILE_PATHS:-}\"\n"
        "    fi\n"
        "    if [ -z \"$selected\" ]; then\n"
        "        selected=\"${CAJA_SCRIPT_SELECTED_FILE_PATHS:-}\"\n"
        "    fi\n"
        "\n"
        "    while IFS= read -r selected_path; do\n"
        "        if [ -n \"$selected_path\" ]; then\n"
        "            paths+=(\"$selected_path\")\n"
        "        fi\n"
        "    done <<< \"$selected\"\n"
        "fi\n"
        "\n"
        "if [ \"${#paths[@]}\" -gt 0 ]; then\n"
        f"    {command} \"${{paths[@]}}\" "
        ">/dev/null 2>&1 &\n"
        "fi\n"
    )


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
