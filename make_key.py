import os
import shutil
import sys
import winreg as reg


is_packaged = getattr(sys, "frozen", False)

cwd = os.path.dirname(os.path.abspath(__file__))
python_exe = sys.executable

FILE_NAME = "\\shell\\UwUConverter"
FILE_PATH_START = (
    "Software\\Classes\\SystemFileAssociations\\"
)

FOLDER_MENU_PATH = (
    "Software\\Classes\\Directory"
    "\\shell\\UwUConverter"
)

app_folder = os.path.join(
    os.environ["LOCALAPPDATA"],
    "UwUConverter"
)

saved_icon = os.path.join(
    app_folder,
    "icon.ico"
)

icon_value = f'"{saved_icon}",0'


def FindPythonw():
    candidates = [
        os.path.join(
            os.path.dirname(python_exe),
            "pythonw.exe"
        ),
        os.path.join(
            sys.base_prefix,
            "pythonw.exe"
        ),
    ]

    base_executable = getattr(
        sys,
        "_base_executable",
        None
    )

    if base_executable:
        candidates.append(
            os.path.join(
                os.path.dirname(base_executable),
                "pythonw.exe"
            )
        )

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate

    return python_exe


def SaveIcon():
    os.makedirs(app_folder, exist_ok=True)

    source_icon = os.path.join(
        cwd,
        "UwUConverter.ico"
    )

    if os.path.isfile(source_icon):
        shutil.copy2(
            source_icon,
            saved_icon
        )


def CreateExtensions(file_types):
    SaveIcon()

    for extension, conversions in file_types.items():
        ResetExtension(extension)

        if conversions:
            AddExtension(
                extension,
                conversions
            )

    ResetFolderMenu()
    AddFolderMenu()


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
                    child_name = reg.EnumKey(
                        key,
                        0
                    )

                    DeleteTree(
                        root,
                        key_path
                        + "\\"
                        + child_name
                    )

                except OSError:
                    break

        reg.DeleteKey(root, key_path)

    except FileNotFoundError:
        pass


def ResetExtension(file_type):
    DeleteTree(
        reg.HKEY_CURRENT_USER,
        FILE_PATH_START
        + file_type
        + FILE_NAME
    )


def ResetFolderMenu():
    DeleteTree(
        reg.HKEY_CURRENT_USER,
        FOLDER_MENU_PATH
    )


def command_string(convert_type):
    if is_packaged:
        if convert_type == "BATCH_UI_ALL":
            batch_executable = os.path.join(
                os.path.dirname(sys.executable),
                "UwUConverterBatch.exe"
            )

            if os.path.isfile(batch_executable):
                return (
                    f'"{batch_executable}" '
                    f'"%1"'
                )

        return (
            f'"{sys.executable}" '
            f'"%1" '
            f'"{convert_type}"'
        )

    pythonw_exe = FindPythonw()

    if convert_type == "BATCH_UI_ALL":
        batch_script = os.path.join(
            cwd,
            "BatchLauncher.py"
        )

        return (
            f'"{pythonw_exe}" '
            f'"{batch_script}" '
            f'"%1"'
        )

    converter_script = os.path.join(
        cwd,
        "Converter.py"
    )

    return (
        f'"{pythonw_exe}" '
        f'"{converter_script}" '
        f'"%1" '
        f'"{convert_type}"'
    )


def CreateCommand(command_path, convert_type):
    with reg.CreateKey(
        reg.HKEY_CURRENT_USER,
        command_path
    ) as command_key:
        reg.SetValueEx(
            command_key,
            "",
            0,
            reg.REG_SZ,
            command_string(convert_type)
        )


def CreateMenuItems(parent_path, items):
    for item_id, menu_text, action in items:
        item_path = (
            parent_path
            + "\\shell\\"
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
                item_path + "\\command",
                action
            )


def AddExtension(file_type, conversions):
    key_path = (
        FILE_PATH_START
        + file_type
        + FILE_NAME
    )

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


def AddFolderMenu():
    with reg.CreateKey(
        reg.HKEY_CURRENT_USER,
        FOLDER_MENU_PATH
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

    CreateCommand(
        FOLDER_MENU_PATH + "\\command",
        "BATCH_UI_ALL"
    )


def RemoveExtensions(file_types):
    for extension in file_types:
        ResetExtension(extension)

    ResetFolderMenu()

    if os.path.isfile(saved_icon):
        os.remove(saved_icon)

    try:
        os.rmdir(app_folder)
    except OSError:
        pass
