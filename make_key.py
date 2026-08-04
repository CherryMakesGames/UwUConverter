import winreg as reg
import os
import sys
import shutil

is_packaged = getattr(sys, "frozen", False)

cwd = os.path.dirname(os.path.abspath(__file__))
python_exe = sys.executable

name = r"\\shell\\UwUConverter"
path_start = r"Software\\Classes\\SystemFileAssociations\\"

app_folder = os.path.join(
    os.environ["LOCALAPPDATA"],
    "UwUConverter"
)

saved_icon = os.path.join(
    app_folder,
    "icon.ico"
)

icon_value = f'"{saved_icon}",0'


def SaveIcon():
    os.makedirs(app_folder, exist_ok=True)

    source_icon = os.path.join(
        cwd,
        "UwUConverter.ico"
    )

    shutil.copy2(
        source_icon,
        saved_icon
    )


def CreateExtensions(file_types):
    SaveIcon()

    for extension, conversions in file_types.items():
        ResetExtension(extension)

        if conversions:
            AddExtension(extension, conversions)


def DeleteTree(root, key_path):
    try:
        with reg.OpenKey(
            root,
            key_path,
            0,
            reg.KEY_READ | reg.KEY_WRITE
        ) as key:
            while True:
                try:
                    child_name = reg.EnumKey(key, 0)

                    DeleteTree(
                        root,
                        key_path + r"\\" + child_name
                    )

                except OSError:
                    break

        reg.DeleteKey(root, key_path)

    except FileNotFoundError:
        pass


def ResetExtension(file_type):
    key_path = path_start + file_type + name

    DeleteTree(
        reg.HKEY_CURRENT_USER,
        key_path
    )


def CreateCommand(command_path, convert_type):
    if is_packaged:
        command = (
            f'"{sys.executable}" '
            f'"%1" '
            f'"{convert_type}"'
        )
    else:
        converter_script = os.path.join(
            cwd,
            "Converter.py"
        )

        command = (
            f'"{python_exe}" '
            f'"{converter_script}" '
            f'"%1" '
            f'"{convert_type}"'
        )

    with reg.CreateKey(
        reg.HKEY_CURRENT_USER,
        command_path
    ) as command_key:
        reg.SetValueEx(
            command_key,
            "",
            0,
            reg.REG_SZ,
            command
        )


def CreateMenuItems(parent_path, items):
    for item_id, menu_text, action in items:
        item_path = (
            parent_path
            + r"\\shell\\"
            + item_id
        )

        with reg.CreateKey(
            reg.HKEY_CURRENT_USER,
            item_path
        ) as item_key:
            reg.SetValueEx(
                item_key,
                "MUIVerb",
                0,
                reg.REG_SZ,
                menu_text
            )

            reg.SetValueEx(
                item_key,
                "Icon",
                0,
                reg.REG_SZ,
                icon_value
            )

            if isinstance(action, list):
                reg.SetValueEx(
                    item_key,
                    "SubCommands",
                    0,
                    reg.REG_SZ,
                    ""
                )

        if isinstance(action, list):
            CreateMenuItems(
                item_path,
                action
            )
        else:
            CreateCommand(
                item_path + r"\\command",
                action
            )


def AddExtension(file_type, conversions):
    key_path = path_start + file_type + name

    with reg.CreateKey(
        reg.HKEY_CURRENT_USER,
        key_path
    ) as key:
        reg.SetValueEx(
            key,
            "MUIVerb",
            0,
            reg.REG_SZ,
            "Convert With UwUConverter ^-^"
        )

        reg.SetValueEx(
            key,
            "Icon",
            0,
            reg.REG_SZ,
            icon_value
        )

        reg.SetValueEx(
            key,
            "SubCommands",
            0,
            reg.REG_SZ,
            ""
        )

    CreateMenuItems(
        key_path,
        conversions
    )


def RemoveExtensions(file_types):
    for extension in file_types:
        ResetExtension(extension)

    if os.path.isfile(saved_icon):
        os.remove(saved_icon)

    try:
        os.rmdir(app_folder)
    except OSError:
        pass
