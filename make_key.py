import winreg as reg
import os
import sys

cwd = os.getcwd()

python_exe = sys.executable

name = r"\\shell\\UwUConverter"

path_start = r"Software\\Classes\\SystemFileAssociations\\"

def CreateExtensions(file_types):
    for extension, conversions in file_types.items():
        ResetExtension(extension)
        AddExtension(extension, conversions)

def DeleteTree(root, key_path):
    try:
        with reg.OpenKey(root, key_path, 0, reg.KEY_READ | reg.KEY_WRITE) as key:
            while True:
                try:
                    child_name = reg.EnumKey(key, 0)
                    DeleteTree(root, key_path + r"\\" + child_name)
                except OSError:
                    break

        reg.DeleteKey(root, key_path)

    except FileNotFoundError:
        pass

def ResetExtension(file_type):
    key_path = path_start + file_type + name
    DeleteTree(reg.HKEY_CURRENT_USER, key_path)
    

def AddExtension(file_type, conversions):
    key_path = path_start + file_type + name

    with reg.CreateKey(reg.HKEY_CURRENT_USER, key_path) as key:
        reg.SetValueEx(key, "MUIVerb", 0, reg.REG_SZ, "Convert With UwUConverter ^-^")

        reg.SetValueEx(
            key,
            "SubCommands",
            0,
            reg.REG_SZ,
            ""
        )

    for conversion_id, menu_text, convert_type in conversions:
        conversion_path = key_path + r"\\shell\\" + conversion_id

        with reg.CreateKey(reg.HKEY_CURRENT_USER, conversion_path) as conversion_key:
            reg.SetValueEx(conversion_key, "MUIVerb", 0, reg.REG_SZ, menu_text)

        command_path = conversion_path + r"\\command"

        command = (
            f'"{python_exe}" '
            f'"{cwd}\\Converter.py" '
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