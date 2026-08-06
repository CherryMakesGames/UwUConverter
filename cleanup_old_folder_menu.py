import winreg as reg


COMMAND_STORE_ROOT = (
    "Software\\Microsoft\\Windows\\CurrentVersion"
    "\\Explorer\\CommandStore\\shell"
)


def delete_tree(root, path):
    try:
        with reg.OpenKey(
            root,
            path,
            0,
            reg.KEY_READ | reg.KEY_WRITE
        ) as key:
            while True:
                try:
                    child = reg.EnumKey(key, 0)
                    delete_tree(
                        root,
                        path + "\\" + child
                    )
                except OSError:
                    break

        reg.DeleteKey(root, path)
        print("Removed:", path)

    except FileNotFoundError:
        pass


delete_tree(
    reg.HKEY_CURRENT_USER,
    "Software\\Classes\\Directory"
    "\\shell\\UwUConverter"
)

classes_root = "Software\\Classes"

try:
    with reg.OpenKey(
        reg.HKEY_CURRENT_USER,
        classes_root,
        0,
        reg.KEY_READ
    ) as key:
        names = []
        index = 0

        while True:
            try:
                names.append(reg.EnumKey(key, index))
                index += 1
            except OSError:
                break

    for name in names:
        if name.startswith("UwUConverter.Batch."):
            delete_tree(
                reg.HKEY_CURRENT_USER,
                classes_root + "\\" + name
            )
except FileNotFoundError:
    pass

try:
    with reg.OpenKey(
        reg.HKEY_CURRENT_USER,
        COMMAND_STORE_ROOT,
        0,
        reg.KEY_READ
    ) as key:
        names = []
        index = 0

        while True:
            try:
                names.append(reg.EnumKey(key, index))
                index += 1
            except OSError:
                break

    for name in names:
        if name.startswith("UwUConverter.Batch"):
            delete_tree(
                reg.HKEY_CURRENT_USER,
                COMMAND_STORE_ROOT + "\\" + name
            )
except FileNotFoundError:
    pass

print("All old UwUConverter batch menu entries removed.")
