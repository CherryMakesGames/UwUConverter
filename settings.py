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

def settings_path():
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "UwUConverter"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home()/".config"))) / "UwUConverter"
    return base / "settings.ini"

def load_settings(path=None):
    config = configparser.ConfigParser()
    config.read(str(path or settings_path()), encoding="utf-8")
    return config

def enabled(category, config=None):
    config = config if config is not None else load_settings()
    return config.getboolean("ContextMenu", category, fallback=True)

def get_bool(section, key, default=True, config=None):
    config = config if config is not None else load_settings()
    return config.getboolean(section, key, fallback=default)

def save_settings(config, path=None):
    target = Path(path or settings_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as stream:
        config.write(stream)
    return target

def category_for_action(action, extension=None):
    action = str(action).lower()
    if action == "archive_create_zip_prompt":
        return "archive"
    if action.startswith("archive_"):
        return "archive"
    if action.startswith("batch_") or action == "batch_ui_all":
        return "batch"
    if "compress" in action:
        return "compression"
    if action.startswith("model_"):
        return "model"
    if action.startswith("document_"):
        return "document"
    if action.startswith("spreadsheet_"):
        return "spreadsheet"
    extension = str(extension or "").lower()
    if extension in {".png", ".jpg", ".jpeg", ".webp", ".ico", ".raw", ".tif", ".tiff"}:
        return "image"
    if extension in {".mp4", ".mov", ".mkv", ".avi", ".webm"}:
        return "video" if action in {"mp4", "mkv", "mov", "avi", "webm"} else "audio"
    if extension in {".mp3", ".wav", ".flac", ".opus", ".ogg"}:
        return "audio"
    if extension in {".pdf", ".docx", ".odt", ".txt"}:
        return "document"
    if extension in {".xlsx", ".xls", ".xlsb", ".xlsm", ".ods", ".csv", ".tsv"}:
        return "spreadsheet"
    if extension in {".obj", ".stl", ".ply", ".glb"}:
        return "model"
    return "image" if action in {"png", "jpg", "jpeg", "webp", "ico", "tif", "tiff"} else "audio"

def filter_file_types(file_types, config=None):
    config = config if config is not None else load_settings()
    def filter_items(items, extension):
        filtered = []
        for identifier, label, item in items:
            if isinstance(item, list):
                children = filter_items(item, extension)
                if children:
                    filtered.append((identifier, label, children))
            elif enabled(category_for_action(item, extension), config):
                filtered.append((identifier, label, item))
        return filtered
    return {ext: filter_items(items, ext) for ext, items in file_types.items()}
