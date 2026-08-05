import pathlib
import shlex
import shutil
import stat
import sys


APP_FOLDER_NAME = "UwUConverter"

SCRIPT_FOLDERS = {
    "Nautilus": pathlib.Path.home() / ".local/share/nautilus/scripts",
    "Nemo": pathlib.Path.home() / ".local/share/nemo/scripts",
    "Caja": pathlib.Path.home() / ".config/caja/scripts",
}

DOLPHIN_FOLDER = (
    pathlib.Path.home()
    / ".local/share/kio/servicemenus"
)

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
    ".ico": "image/vnd.microsoft.icon",
    ".raw": "application/octet-stream",
    ".pdf": "application/pdf",
    ".docx": (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ),
    ".txt": "text/plain",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".xlsx": (
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    ),
    ".xls": "application/vnd.ms-excel",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".csv": "text/csv",
    ".xlsb": (
        "application/vnd.ms-excel.sheet.binary."
        "macroEnabled.12"
    ),
    ".xlsm": (
        "application/vnd.ms-excel.sheet."
        "macroEnabled.12"
    ),
    ".tsv": "text/tab-separated-values",
}


def CreateExtensions(file_types):
    actions = collect_actions(file_types)

    for manager, folder in SCRIPT_FOLDERS.items():
        app_folder = folder / APP_FOLDER_NAME

        if app_folder.exists():
            shutil.rmtree(app_folder)

        create_script_menus(
            app_folder,
            actions
        )

        print(
            f"Installed {manager} scripts: "
            f"{app_folder}"
        )

    create_dolphin_menus(actions)

    print(
        "Installed Dolphin service menus: "
        + str(DOLPHIN_FOLDER)
    )


def RemoveExtensions(file_types=None):
    for folder in SCRIPT_FOLDERS.values():
        app_folder = folder / APP_FOLDER_NAME

        if app_folder.exists():
            shutil.rmtree(app_folder)

    if DOLPHIN_FOLDER.exists():
        for file in DOLPHIN_FOLDER.glob(
            "uwuconverter-*.desktop"
        ):
            file.unlink()

    print("Removed UwUConverter Linux menus.")


def collect_actions(file_types):
    actions = {}

    for extension, items in file_types.items():
        collect_items(
            items,
            extension,
            default_group(extension),
            actions
        )

    return actions


def collect_items(
    items,
    extension,
    group_name,
    actions
):
    for _, label, action in items:
        if isinstance(action, list):
            collect_items(
                action,
                extension,
                label,
                actions
            )
        else:
            key = (
                group_name,
                label,
                action
            )

            actions.setdefault(
                key,
                set()
            ).add(extension.lower())


def default_group(extension):
    if extension in {
        ".mp4", ".mkv", ".mov", ".avi", ".webm"
    }:
        return "Video Conversions"

    if extension in {
        ".mp3", ".wav", ".ogg", ".flac", ".opus"
    }:
        return "Music Conversions"

    if extension in {
        ".png", ".jpg", ".jpeg", ".webp", ".ico", ".raw"
    }:
        return "Image Conversions"

    if extension in {
        ".pdf", ".docx", ".txt", ".odt"
    }:
        return "Document Conversions"

    return "Spreadsheet Conversions"


def create_script_menus(app_folder, actions):
    for (
        group_name,
        label,
        action
    ), extensions in sorted(actions.items()):
        group_folder = (
            app_folder
            / safe_name(group_name)
        )

        group_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        script = (
            group_folder
            / safe_name(label)
        )

        script.write_text(
            build_shell_script(
                action,
                extensions
            ),
            encoding="utf-8"
        )

        make_executable(script)


def create_dolphin_menus(actions):
    DOLPHIN_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    for old_file in DOLPHIN_FOLDER.glob(
        "uwuconverter-*.desktop"
    ):
        old_file.unlink()

    grouped = {}

    for (
        group_name,
        label,
        action
    ), extensions in actions.items():
        grouped.setdefault(
            group_name,
            []
        ).append(
            (
                label,
                action,
                extensions
            )
        )

    for group_name, group_actions in grouped.items():
        file = (
            DOLPHIN_FOLDER
            / (
                "uwuconverter-"
                + slug(group_name)
                + ".desktop"
            )
        )

        file.write_text(
            build_dolphin_file(
                group_name,
                group_actions
            ),
            encoding="utf-8"
        )

        make_executable(file)


def build_dolphin_file(
    group_name,
    group_actions
):
    action_ids = []
    mime_types = set()
    sections = []

    command = " ".join(
        shlex.quote(part)
        for part in converter_command()
    )

    for index, (
        label,
        action,
        extensions
    ) in enumerate(
        sorted(group_actions),
        start=1
    ):
        action_id = (
            f"action{index}_"
            + slug(action)
        )

        action_ids.append(action_id)

        for extension in extensions:
            mime_type = MIME_TYPES.get(
                extension
            )

            if mime_type:
                mime_types.add(mime_type)

        sections.append(
            "\n".join(
                [
                    (
                        "[Desktop Action "
                        + action_id
                        + "]"
                    ),
                    "Name=" + label,
                    "Icon=document-convert",
                    (
                        "Exec="
                        + command
                        + " %F "
                        + shlex.quote(action)
                    ),
                ]
            )
        )

    header = "\n".join(
        [
            "[Desktop Entry]",
            "Type=Service",
            (
                "MimeType="
                + ";".join(
                    sorted(mime_types)
                )
                + ";"
            ),
            (
                "Actions="
                + ";".join(action_ids)
                + ";"
            ),
            (
                "X-KDE-Submenu=UwUConverter - "
                + group_name
            ),
            "X-KDE-Priority=TopLevel",
        ]
    )

    return (
        header
        + "\n\n"
        + "\n\n".join(sections)
        + "\n"
    )


def build_shell_script(
    action,
    extensions
):
    command = " ".join(
        shlex.quote(part)
        for part in converter_command()
    )

    extension_cases = "|".join(
        extension.removeprefix(".")
        for extension in sorted(extensions)
    )

    return (
        "#!/usr/bin/env bash\n"
        "set -u\n"
        "for file_path in \"$@\"; do\n"
        "    extension=\"${file_path##*.}\"\n"
        "    extension=\"${extension,,}\"\n"
        "    case \"$extension\" in\n"
        f"        {extension_cases})\n"
        f"            {command} \"$file_path\" "
        f"{shlex.quote(action)}\n"
        "            ;;\n"
        "    esac\n"
        "done\n"
    )


def converter_command():
    if getattr(sys, "frozen", False):
        return [sys.executable]

    converter = (
        pathlib.Path(__file__)
        .resolve()
        .parent
        / "Converter.py"
    )

    return [
        sys.executable,
        str(converter)
    ]


def make_executable(path):
    path.chmod(
        path.stat().st_mode
        | stat.S_IXUSR
        | stat.S_IXGRP
        | stat.S_IXOTH
    )


def safe_name(value):
    return value.replace("/", "_").strip()


def slug(value):
    result = []

    for character in value.lower():
        if character.isalnum():
            result.append(character)
        elif result and result[-1] != "-":
            result.append("-")

    return (
        "".join(result).strip("-")
        or "menu"
    )
