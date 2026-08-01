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
        AddExtension(extension)

def ResetExtension(file_type):
    key_path = path_start + file_type + name

    try:
        reg.DeleteKey(
            reg.HKEY_CURRENT_USER,
            key_path + r"\\command"
        )
    except FileNotFoundError:
        pass

    try:
        reg.DeleteKey(
            reg.HKEY_CURRENT_USER,
            key_path
        )
    except FileNotFoundError:
        pass
    

def AddExtension(file_type):
    key_path = path_start + file_type + name
    reg.CreateKey(reg.HKEY_CURRENT_USER, key_path)