import json
import pathlib
import shutil
import sys


HOST_NAME = "com.uwuconverter.browser"
CHROMIUM_EXTENSION_ID = "gdopoipkbfpeojmblonjjmkflahgfihg"
FIREFOX_EXTENSION_ID = "uwuconverter@pinksakurastudios.com"


WINDOWS_CHROMIUM_REGISTRY_PATHS = [
    # Chrome-compatible registration. Opera's own Native Messaging
    # documentation explicitly points Windows native hosts here, so this
    # also covers Opera and Opera GX.
    r"Software\Google\Chrome\NativeMessagingHosts",

    r"Software\Chromium\NativeMessagingHosts",
    r"Software\Microsoft\Edge\NativeMessagingHosts",

    # Chromium-family compatibility mirrors. These do not replace the
    # Google/Chromium keys above; they make the host directly discoverable
    # by browsers that use their own vendor registry branch.
    r"Software\BraveSoftware\Brave-Browser\NativeMessagingHosts",
    r"Software\Vivaldi\NativeMessagingHosts",
]

LINUX_CHROMIUM_MANIFEST_DIRS = [
    # Google Chrome family
    pathlib.Path.home()
    / ".config/google-chrome/NativeMessagingHosts",
    pathlib.Path.home()
    / ".config/google-chrome-beta/NativeMessagingHosts",
    pathlib.Path.home()
    / ".config/google-chrome-unstable/NativeMessagingHosts",
    pathlib.Path.home()
    / ".config/google-chrome-for-testing/NativeMessagingHosts",

    # Chromium
    pathlib.Path.home()
    / ".config/chromium/NativeMessagingHosts",

    # Microsoft Edge family
    pathlib.Path.home()
    / ".config/microsoft-edge/NativeMessagingHosts",
    pathlib.Path.home()
    / ".config/microsoft-edge-beta/NativeMessagingHosts",
    pathlib.Path.home()
    / ".config/microsoft-edge-dev/NativeMessagingHosts",

    # Opera desktop family. Opera GX currently uses the same Chromium
    # extension package on supported desktop platforms; on Windows it is
    # covered by the Chrome-compatible registry registration above.
    pathlib.Path.home()
    / ".config/opera/NativeMessagingHosts",
    pathlib.Path.home()
    / ".config/opera-beta/NativeMessagingHosts",
    pathlib.Path.home()
    / ".config/opera-developer/NativeMessagingHosts",
    pathlib.Path.home()
    / ".config/opera-gx/NativeMessagingHosts",
    pathlib.Path.home()
    / ".config/opera-gx-developer/NativeMessagingHosts",

    # Opera/Opera GX Flatpak profile candidates. The sandbox can still
    # restrict execution of an external native host; browser_setup.py warns
    # Flatpak users about that case.
    pathlib.Path.home()
    / ".var/app/com.opera.Opera/config/opera/NativeMessagingHosts",
    pathlib.Path.home()
    / ".var/app/com.opera.Opera/config/google-chrome/NativeMessagingHosts",
    pathlib.Path.home()
    / ".var/app/com.opera.opera-gx/config/opera-gx/NativeMessagingHosts",
    pathlib.Path.home()
    / ".var/app/com.opera.opera-gx/config/google-chrome/NativeMessagingHosts",

    # Brave
    pathlib.Path.home()
    / ".config/BraveSoftware/Brave-Browser/NativeMessagingHosts",
    pathlib.Path.home()
    / ".config/BraveSoftware/Brave-Browser-Beta/NativeMessagingHosts",
    pathlib.Path.home()
    / ".config/BraveSoftware/Brave-Browser-Dev/NativeMessagingHosts",

    # Vivaldi
    pathlib.Path.home()
    / ".config/vivaldi/NativeMessagingHosts",
    pathlib.Path.home()
    / ".config/vivaldi-snapshot/NativeMessagingHosts",

    # Common Flatpak Chromium-family profile locations.
    pathlib.Path.home()
    / ".var/app/org.chromium.Chromium/config/chromium/NativeMessagingHosts",
    pathlib.Path.home()
    / ".var/app/com.google.Chrome/config/google-chrome/NativeMessagingHosts",
    pathlib.Path.home()
    / ".var/app/com.brave.Browser/config/BraveSoftware/Brave-Browser/NativeMessagingHosts",
    pathlib.Path.home()
    / ".var/app/com.vivaldi.Vivaldi/config/vivaldi/NativeMessagingHosts",
]

LINUX_FIREFOX_MANIFEST_DIR = (
    pathlib.Path.home()
    / ".mozilla/native-messaging-hosts"
)


def _application_directory():
    if getattr(sys, "frozen", False):
        return pathlib.Path(
            sys.executable
        ).resolve().parent

    return pathlib.Path(__file__).resolve().parent


def _host_path():
    application_directory = _application_directory()

    if sys.platform == "win32":
        return (
            application_directory
            / "UwUConverterBrowserHost.exe"
        )

    return (
        application_directory
        / "UwUConverterBrowserHost"
    )


def _manifest_directory():
    return (
        _application_directory()
        / "browser-native"
    )


def _chromium_manifest_path():
    return (
        _manifest_directory()
        / (HOST_NAME + ".chromium.json")
    )


def _firefox_manifest_path():
    return (
        _manifest_directory()
        / (HOST_NAME + ".firefox.json")
    )


def _write_json(path, data):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            data,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def _write_manifests(host_path):
    manifest_directory = _manifest_directory()
    manifest_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    chromium_manifest = {
        "name": HOST_NAME,
        "description": (
            "UwUConverter browser integration host"
        ),
        "path": str(host_path),
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://"
            + CHROMIUM_EXTENSION_ID
            + "/"
        ],
    }

    firefox_manifest = {
        "name": HOST_NAME,
        "description": (
            "UwUConverter browser integration host"
        ),
        "path": str(host_path),
        "type": "stdio",
        "allowed_extensions": [
            FIREFOX_EXTENSION_ID
        ],
    }

    _write_json(
        _chromium_manifest_path(),
        chromium_manifest,
    )
    _write_json(
        _firefox_manifest_path(),
        firefox_manifest,
    )


def _register_windows():
    import winreg

    chromium_manifest = str(
        _chromium_manifest_path()
    )
    firefox_manifest = str(
        _firefox_manifest_path()
    )

    for registry_root in (
        WINDOWS_CHROMIUM_REGISTRY_PATHS
    ):
        key_path = (
            registry_root
            + "\\"
            + HOST_NAME
        )

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
        ) as key:
            winreg.SetValueEx(
                key,
                "",
                0,
                winreg.REG_SZ,
                chromium_manifest,
            )

    firefox_key_path = (
        "Software\\Mozilla\\NativeMessagingHosts\\"
        + HOST_NAME
    )

    with winreg.CreateKey(
        winreg.HKEY_CURRENT_USER,
        firefox_key_path,
    ) as key:
        winreg.SetValueEx(
            key,
            "",
            0,
            winreg.REG_SZ,
            firefox_manifest,
        )


def _register_linux():
    chromium_source = _chromium_manifest_path()
    firefox_source = _firefox_manifest_path()

    for directory in (
        LINUX_CHROMIUM_MANIFEST_DIRS
    ):
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )
        shutil.copy2(
            chromium_source,
            directory / (HOST_NAME + ".json"),
        )

    LINUX_FIREFOX_MANIFEST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    shutil.copy2(
        firefox_source,
        LINUX_FIREFOX_MANIFEST_DIR
        / (HOST_NAME + ".json"),
    )


def RegisterBrowserIntegration():
    host_path = _host_path()

    if not host_path.is_file():
        print(
            "UwUConverter browser host is not built; "
            "skipping browser native-messaging registration."
        )
        return False

    if not sys.platform == "win32":
        try:
            host_path.chmod(
                host_path.stat().st_mode | 0o111
            )
        except OSError:
            pass

    _write_manifests(host_path)

    if sys.platform == "win32":
        _register_windows()
    elif sys.platform.startswith("linux"):
        _register_linux()
    else:
        return False

    print(
        "Installed UwUConverter browser native-messaging host."
    )
    return True


def _delete_windows_registry_key(
    winreg,
    key_path,
):
    try:
        winreg.DeleteKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
        )
    except FileNotFoundError:
        pass


def _unregister_windows():
    import winreg

    for registry_root in (
        WINDOWS_CHROMIUM_REGISTRY_PATHS
    ):
        _delete_windows_registry_key(
            winreg,
            registry_root
            + "\\"
            + HOST_NAME,
        )

    _delete_windows_registry_key(
        winreg,
        "Software\\Mozilla\\NativeMessagingHosts\\"
        + HOST_NAME,
    )


def _unregister_linux():
    for directory in (
        LINUX_CHROMIUM_MANIFEST_DIRS
    ):
        try:
            (
                directory
                / (HOST_NAME + ".json")
            ).unlink()
        except FileNotFoundError:
            pass

    try:
        (
            LINUX_FIREFOX_MANIFEST_DIR
            / (HOST_NAME + ".json")
        ).unlink()
    except FileNotFoundError:
        pass


def RemoveBrowserIntegration():
    if sys.platform == "win32":
        _unregister_windows()
    elif sys.platform.startswith("linux"):
        _unregister_linux()

    try:
        shutil.rmtree(
            _manifest_directory()
        )
    except FileNotFoundError:
        pass

    print(
        "Removed UwUConverter browser native-messaging registration."
    )
