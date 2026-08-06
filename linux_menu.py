import pathlib
import shlex
import shutil
import stat
import sys

from batch_menus import BATCH_MENUS


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

        create_batch_scripts(
            app_folder,
            BATCH_MENUS
        )

        print(
            f"Installed {manager} batch scripts: "
            f"{app_folder}"
        )

    create_dolphin_batch_menus(
        BATCH_MENUS
    )

    print(
        "Installed Dolphin batch menus: "
        + str(DOLPHIN_FOLDER)
    )


def RemoveExtensions(file_types=None):
    for root in SCRIPT_FOLDERS.values():
        app_folder = root / APP_FOLDER_NAME

        if app_folder.exists():
            shutil.rmtree(app_folder)

    if DOLPHIN_FOLDER.exists():
        for path in DOLPHIN_FOLDER.glob(
            "uwuconverter-batch-*.desktop"
        ):
            path.unlink()

    print(
        "Removed UwUConverter Linux menus."
    )


def create_batch_scripts(root, items):
    for item_id, label, action in items:
        path = root / safe_name(label)

        if isinstance(action, list):
            create_batch_scripts(
                path,
                action
            )
            continue

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        path.write_text(
            build_folder_script(action),
            encoding="utf-8"
        )

        make_executable(path)


def build_folder_script(action):
    command = " ".join(
        shlex.quote(part)
        for part in converter_command()
    )

    return (
        "#!/usr/bin/env bash\n"
        "set -u\n"
        "for folder_path in \"$@\"; do\n"
        "    if [ -d \"$folder_path\" ]; then\n"
        f"        {command} \"$folder_path\" "
        f"{shlex.quote(action)}\n"
        "    fi\n"
        "done\n"
    )


def create_dolphin_batch_menus(items):
    DOLPHIN_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    for old in DOLPHIN_FOLDER.glob(
        "uwuconverter-batch-*.desktop"
    ):
        old.unlink()

    for _, category_label, modes in items:
        for _, mode_label, formats in modes:
            filename = (
                "uwuconverter-batch-"
                + slug(category_label)
                + "-"
                + slug(mode_label)
                + ".desktop"
            )

            path = DOLPHIN_FOLDER / filename

            path.write_text(
                build_dolphin_menu(
                    category_label,
                    mode_label,
                    formats
                ),
                encoding="utf-8"
            )

            make_executable(path)


def build_dolphin_menu(
    category_label,
    mode_label,
    formats
):
    command = " ".join(
        shlex.quote(part)
        for part in converter_command()
    )

    action_ids = []
    sections = []

    for index, (_, label, action) in enumerate(
        formats,
        start=1
    ):
        action_id = (
            f"format{index}_"
            + slug(label)
        )
        action_ids.append(action_id)

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
                        + " %f "
                        + shlex.quote(action)
                    ),
                ]
            )
        )

    header = "\n".join(
        [
            "[Desktop Entry]",
            "Type=Service",
            "MimeType=inode/directory;",
            (
                "Actions="
                + ";".join(action_ids)
                + ";"
            ),
            (
                "X-KDE-Submenu=UwUConverter - "
                + category_label
                + " - "
                + mode_label
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
    return (
        value.replace("/", "_").strip()
        or "Unnamed"
    )


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
