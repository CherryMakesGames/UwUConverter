import winreg as reg
import os
import sys
import shutil

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
    print("SaveIcon started")

    print("LOCALAPPDATA:", os.environ.get("LOCALAPPDATA"))
    print("App folder:", app_folder)

    os.makedirs(app_folder, exist_ok=True)

    print("Folder exists:", os.path.isdir(app_folder))

    source_icon = os.path.join(
        cwd,
        "UwUConverter.ico"
    )

    print("Source icon:", source_icon)
    print("Source exists:", os.path.isfile(source_icon))

    shutil.copy2(
        source_icon,
        saved_icon
    )

    print("Saved icon:", saved_icon)
    print("Saved icon exists:", os.path.isfile(saved_icon))


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

    for conversion_id, menu_text, convert_type in conversions:
        conversion_path = (
            key_path
            + r"\\shell\\"
            + conversion_id
        )

        with reg.CreateKey(
            reg.HKEY_CURRENT_USER,
            conversion_path
        ) as conversion_key:
            reg.SetValueEx(
                conversion_key,
                "MUIVerb",
                0,
                reg.REG_SZ,
                menu_text
            )

            reg.SetValueEx(
                conversion_key,
                "Icon",
                0,
                reg.REG_SZ,
                icon_value
            )

        command_path = (
            conversion_path
            + r"\\command"
        )

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