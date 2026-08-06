import sys


def CreateExtensions(file_types):
    if sys.platform == "win32":
        import make_key
        make_key.CreateExtensions(file_types)
        return

    if sys.platform.startswith("linux"):
        import linux_menu
        linux_menu.CreateExtensions(file_types)
        return

    raise NotImplementedError(
        "Menu installation is not supported on "
        + sys.platform
    )


def RemoveExtensions(file_types):
    if sys.platform == "win32":
        import make_key
        make_key.RemoveExtensions(file_types)
        return

    if sys.platform.startswith("linux"):
        import linux_menu
        linux_menu.RemoveExtensions(file_types)
        return

    raise NotImplementedError(
        "Menu removal is not supported on "
        + sys.platform
    )
