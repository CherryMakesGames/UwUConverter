import os
import pathlib
import shlex
import shutil
import stat
import sys


APP_FOLDER_NAME = "UwUConverter"

FILE_MANAGER_SCRIPT_FOLDERS = {
    "Nautilus": pathlib.Path.home()
    / ".local/share/nautilus/scripts",
    "Nemo": pathlib.Path.home()
    / ".local/share/nemo/scripts",
    "Caja": pathlib.Path.home()
    / ".config/caja/scripts",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".mov",
    ".avi",
    ".webm",
}

AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".ogg",
    ".flac",
    ".opus",
}

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".ico",
    ".raw",
}

DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".odt",
}

SPREADSHEET_EXTENSIONS = {
    ".xlsx",
    ".xls",
    ".ods",
    ".csv",
    ".xlsb",
    ".xlsm",
    ".tsv",
}


def CreateExtensions(file_types):
    actions = collect_actions(file_types)

    installed_to = []

    for manager_name, scripts_folder in (
        FILE_MANAGER_SCRIPT_FOLDERS.items()
    ):
        app_folder = scripts_folder / APP_FOLDER_NAME

        if app_folder.exists():
            shutil.rmtree(app_folder)

        create_scripts(
            app_folder,
            actions
        )

        installed_to.append(
            f"{manager_name}: {app_folder}"
        )

    print("Installed Linux file-manager scripts:")
    print("\n".join(installed_to))
    print()
    print(
        "The entries appear under the file manager's "
        "Scripts submenu."
    )
    print(
        "Restart the file manager if the scripts do not "
        "appear immediately."
    )


def RemoveExtensions(file_types=None):
    removed = []

    for manager_name, scripts_folder in (
        FILE_MANAGER_SCRIPT_FOLDERS.items()
    ):
        app_folder = scripts_folder / APP_FOLDER_NAME

        if app_folder.exists():
            shutil.rmtree(app_folder)
            removed.append(
                f"{manager_name}: {app_folder}"
            )

    if removed:
        print("Removed Linux file-manager scripts:")
        print("\n".join(removed))
    else:
        print(
            "No UwUConverter Linux scripts were installed."
        )


def collect_actions(file_types):
    actions = {}

    for extension, menu_items in file_types.items():
        default_group = group_for_extension(extension)

        collect_menu_items(
            menu_items,
            extension,
            default_group,
            actions
        )

    return actions


def collect_menu_items(
    menu_items,
    extension,
    current_group,
    actions
):
    for _, display_name, action in menu_items:
        if isinstance(action, list):
            collect_menu_items(
                action,
                extension,
                display_name,
                actions
            )
            continue

        key = (
            current_group,
            display_name,
            action
        )

        if key not in actions:
            actions[key] = set()

        actions[key].add(extension.lower())


def group_for_extension(extension):
    if extension in VIDEO_EXTENSIONS:
        return "Video Conversions"

    if extension in AUDIO_EXTENSIONS:
        return "Music Conversions"

    if extension in IMAGE_EXTENSIONS:
        return "Image Conversions"

    if extension in DOCUMENT_EXTENSIONS:
        return "Document Conversions"

    if extension in SPREADSHEET_EXTENSIONS:
        return "Spreadsheet Conversions"

    return "Other Conversions"


def create_scripts(app_folder, actions):
    for (
        group_name,
        display_name,
        action
    ), extensions in sorted(actions.items()):
        group_folder = (
            app_folder
            / safe_filename(group_name)
        )

        group_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        script_path = (
            group_folder
            / safe_filename(display_name)
        )

        script_path.write_text(
            build_script(
                action,
                extensions
            ),
            encoding="utf-8"
        )

        current_mode = script_path.stat().st_mode

        script_path.chmod(
            current_mode
            | stat.S_IXUSR
            | stat.S_IXGRP
            | stat.S_IXOTH
        )


def build_script(action, extensions):
    command = get_converter_command()

    quoted_command = " ".join(
        shlex.quote(part)
        for part in command
    )

    extension_cases = "|".join(
        extension.removeprefix(".")
        for extension in sorted(extensions)
    )

    return f"""#!/usr/bin/env bash

set -u

converted=0
skipped=0

for file_path in "$@"; do
    if [ ! -f "$file_path" ]; then
        skipped=$((skipped + 1))
        continue
    fi

    extension="${{file_path##*.}}"
    extension="${{extension,,}}"

    case "$extension" in
        {extension_cases})
            {quoted_command} "$file_path" {shlex.quote(action)}
            converted=$((converted + 1))
            ;;
        *)
            skipped=$((skipped + 1))
            ;;
    esac
done

if [ "$converted" -eq 0 ]; then
    message="No supported files were selected."
elif [ "$skipped" -gt 0 ]; then
    message="Converted $converted file(s). Skipped $skipped unsupported item(s)."
else
    message="Converted $converted file(s)."
fi

if command -v notify-send >/dev/null 2>&1; then
    notify-send "UwUConverter" "$message"
else
    printf '%s\\n' "$message"
fi
"""


def get_converter_command():
    if getattr(sys, "frozen", False):
        return [
            sys.executable
        ]

    converter_path = (
        pathlib.Path(__file__)
        .resolve()
        .parent
        / "Converter.py"
    )

    return [
        sys.executable,
        str(converter_path)
    ]


def safe_filename(value):
    invalid_characters = {
        "/",
        "\\",
        "\0",
    }

    cleaned = "".join(
        "_"
        if character in invalid_characters
        else character
        for character in value
    )

    return cleaned.strip() or "Unnamed"
