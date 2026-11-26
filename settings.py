"""User settings shared by Python and the native Windows shell extension."""
import configparser
import os
from pathlib import Path


CATEGORIES = {
    "image": "Image conversions",
    "video": "Video conversions",
    "audio": "Audio conversions",
    "compression": "Compression",
    "archive": "Archive actions",
    "document": "Document conversions",
    "spreadsheet": "Spreadsheet conversions",
    "model": "3D model conversions",
    "batch": "Folder batch conversion",
}

CATEGORY_DESCRIPTIONS = {
    "image": "PNG, JPG, WEBP, TIFF, ICO and other image conversion actions.",
    "video": "MP4, MKV, MOV, AVI and WEBM video conversion actions.",
    "audio": "Audio conversion and audio extraction actions.",
    "compression": "Image and video compression presets.",
    "archive": "Create ZIP, extract archives and open the archive manager.",
    "document": "PDF, DOCX, ODT and TXT conversion actions.",
    "spreadsheet": "Excel, ODS, CSV and TSV conversion actions.",
    "model": "OBJ, STL, PLY and GLB model conversion actions.",
    "batch": "Folder batch-conversion actions.",
}

OPERATION_DEFAULTS = {
    "auto_close_success": True,
    "auto_close_delay": 0.65,
    "detect_duplicates": True,
    "codec_fallback": True,
}

_DEFAULT_CACHE = None
_DEFAULT_CACHE_SIGNATURE = None


def settings_path():
    if os.name == "nt":
        base = (
            Path(
                os.environ.get(
                    "LOCALAPPDATA",
                    str(Path.home()),
                )
            )
            / "UwUConverter"
        )
    else:
        base = (
            Path(
                os.environ.get(
                    "XDG_CONFIG_HOME",
                    str(
                        Path.home()
                        / ".config"
                    ),
                )
            )
            / "UwUConverter"
        )

    return base / "settings.ini"


def load_settings(path=None):
    config = configparser.ConfigParser()
    config.read(
        str(
            path
            or settings_path()
        ),
        encoding="utf-8",
    )
    return config




def _default_settings():
    """Cache the default settings file until it changes on disk."""
    global _DEFAULT_CACHE
    global _DEFAULT_CACHE_SIGNATURE

    path = settings_path()

    try:
        stat = path.stat()
        signature = (stat.st_mtime_ns, stat.st_size)
    except OSError:
        signature = None

    if (
        _DEFAULT_CACHE is None
        or signature != _DEFAULT_CACHE_SIGNATURE
    ):
        _DEFAULT_CACHE = load_settings(path)
        _DEFAULT_CACHE_SIGNATURE = signature

    return _DEFAULT_CACHE


def enabled(
    category,
    config=None,
):
    config = (
        config
        if config is not None
        else _default_settings()
    )

    return config.getboolean(
        "ContextMenu",
        category,
        fallback=True,
    )


def get_bool(
    section,
    key,
    default=True,
    config=None,
):
    config = (
        config
        if config is not None
        else _default_settings()
    )

    return config.getboolean(
        section,
        key,
        fallback=default,
    )


def get_float(
    section,
    key,
    default=0.0,
    config=None,
):
    config = (
        config
        if config is not None
        else _default_settings()
    )

    try:
        return config.getfloat(
            section,
            key,
            fallback=default,
        )
    except (
        ValueError,
        TypeError,
    ):
        return float(
            default
        )


def save_settings(
    config,
    path=None,
):
    target = Path(
        path
        or settings_path()
    )
    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with target.open(
        "w",
        encoding="utf-8",
    ) as stream:
        config.write(
            stream
        )

    if target == settings_path():
        global _DEFAULT_CACHE
        global _DEFAULT_CACHE_SIGNATURE
        _DEFAULT_CACHE = None
        _DEFAULT_CACHE_SIGNATURE = None

    return target


def apply_defaults(
    config=None,
):
    config = (
        config
        if config is not None
        else configparser.ConfigParser()
    )

    if not config.has_section(
        "ContextMenu"
    ):
        config.add_section(
            "ContextMenu"
        )

    for category in CATEGORIES:
        config.set(
            "ContextMenu",
            category,
            "true",
        )

    if not config.has_section(
        "Operations"
    ):
        config.add_section(
            "Operations"
        )

    for key, value in OPERATION_DEFAULTS.items():
        config.set(
            "Operations",
            key,
            str(value).lower(),
        )

    return config


def category_for_action(
    action,
    extension=None,
):
    action = str(
        action
    ).lower()

    if action == "archive_create_zip_prompt":
        return "archive"

    if action.startswith(
        "archive_"
    ):
        return "archive"

    if (
        action.startswith(
            "batch_"
        )
        or action == "batch_ui_all"
    ):
        return "batch"

    if "compress" in action:
        return "compression"

    if action.startswith(
        "model_"
    ):
        return "model"

    if action.startswith(
        "document_"
    ):
        return "document"

    if action.startswith(
        "spreadsheet_"
    ):
        return "spreadsheet"

    extension = str(
        extension
        or ""
    ).lower()

    if extension in {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".ico",
        ".raw",
        ".tif",
        ".tiff",
    }:
        return "image"

    if extension in {
        ".mp4",
        ".mov",
        ".mkv",
        ".avi",
        ".webm",
    }:
        if action in {
            "mp4",
            "mkv",
            "mov",
            "avi",
            "webm",
        }:
            return "video"

        return "audio"

    if extension in {
        ".mp3",
        ".wav",
        ".flac",
        ".opus",
        ".ogg",
    }:
        return "audio"

    if extension in {
        ".pdf",
        ".docx",
        ".odt",
        ".txt",
    }:
        return "document"

    if extension in {
        ".xlsx",
        ".xls",
        ".xlsb",
        ".xlsm",
        ".ods",
        ".csv",
        ".tsv",
    }:
        return "spreadsheet"

    if extension in {
        ".obj",
        ".stl",
        ".ply",
        ".glb",
    }:
        return "model"

    if action in {
        "png",
        "jpg",
        "jpeg",
        "webp",
        "ico",
        "tif",
        "tiff",
    }:
        return "image"

    return "audio"


def filter_file_types(
    file_types,
    config=None,
):
    config = (
        config
        if config is not None
        else load_settings()
    )

    def filter_items(
        items,
        extension,
    ):
        filtered = []

        for (
            identifier,
            label,
            item,
        ) in items:
            if isinstance(
                item,
                list,
            ):
                children = (
                    filter_items(
                        item,
                        extension,
                    )
                )

                if children:
                    filtered.append(
                        (
                            identifier,
                            label,
                            children,
                        )
                    )

            elif enabled(
                category_for_action(
                    item,
                    extension,
                ),
                config,
            ):
                filtered.append(
                    (
                        identifier,
                        label,
                        item,
                    )
                )

        return filtered

    return {
        extension: filter_items(
            items,
            extension,
        )
        for extension, items
        in file_types.items()
    }
