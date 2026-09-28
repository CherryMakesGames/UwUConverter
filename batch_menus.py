IMAGE_FORMATS = [
    ("01_png", "PNG", "PNG"),
    ("02_jpg", "JPG", "JPG"),
    ("03_jpeg", "JPEG", "JPEG"),
    ("04_webp", "WEBP", "WEBP"),
    ("05_ico", "ICO", "ICO"),
    ("06_tif", "TIF", "TIF"),
    ("07_tiff", "TIFF", "TIFF"),
    ("08_pdf", "PDF", "PDF"),
]

VIDEO_FORMATS = [
    ("01_mp4", "MP4", "MP4"),
    ("02_mkv", "MKV", "MKV"),
    ("03_mov", "MOV", "MOV"),
    ("04_avi", "AVI", "AVI"),
    ("05_webm", "WEBM", "WEBM"),
    ("06_mp3", "MP3 Audio", "MP3"),
    ("07_wav", "WAV Audio", "WAV"),
    ("08_flac", "FLAC Audio", "FLAC"),
    ("09_ogg", "OGG Audio", "OGG"),
    ("10_opus", "OPUS Audio", "OPUS"),
]

AUDIO_FORMATS = [
    ("01_mp3", "MP3", "MP3"),
    ("02_wav", "WAV", "WAV"),
    ("03_flac", "FLAC", "FLAC"),
    ("04_ogg", "OGG", "OGG"),
    ("05_opus", "OPUS", "OPUS"),
]

DOCUMENT_FORMATS = [
    ("01_pdf", "PDF", "PDF"),
    ("02_docx", "DOCX", "DOCX"),
    ("03_odt", "ODT", "ODT"),
    ("04_txt", "TXT", "TXT"),
]

SPREADSHEET_FORMATS = [
    ("01_pdf", "PDF", "PDF"),
    ("02_xlsx", "XLSX", "XLSX"),
    ("03_xls", "XLS", "XLS"),
    ("04_ods", "ODS", "ODS"),
    ("05_csv", "CSV", "CSV"),
    ("06_tsv", "TSV", "TSV"),
]



MODEL_FORMATS = [
    ("01_obj", "OBJ", "OBJ"),
    ("02_stl", "STL", "STL"),
    ("03_ply", "PLY", "PLY"),
    ("04_glb", "GLB", "GLB"),
]


def make_modes(category, formats):
    return [
        (
            "01_replace",
            "Replace Originals",
            make_format_actions(
                category,
                "REPLACE",
                formats
            )
        ),
        (
            "02_folder",
            "Create A New Folder",
            make_format_actions(
                category,
                "FOLDER",
                formats
            )
        ),
        (
            "03_beside",
            "Place Beside Originals",
            make_format_actions(
                category,
                "BESIDE",
                formats
            )
        ),
    ]


def make_format_actions(category, mode, formats):
    return [
        (
            item_id,
            label,
            f"BATCH_{category}_{mode}_{format_name}"
        )
        for item_id, label, format_name in formats
    ]


BATCH_MENUS = [
    (
        "01_images",
        "Batch Images",
        make_modes(
            "IMAGE",
            IMAGE_FORMATS
        )
    ),
    (
        "02_video",
        "Batch Video",
        make_modes(
            "VIDEO",
            VIDEO_FORMATS
        )
    ),
    (
        "03_audio",
        "Batch Audio",
        make_modes(
            "AUDIO",
            AUDIO_FORMATS
        )
    ),
    (
        "04_documents",
        "Batch Documents",
        make_modes(
            "DOCUMENT",
            DOCUMENT_FORMATS
        )
    ),
    (
        "05_spreadsheets",
        "Batch Spreadsheets",
        make_modes(
            "SPREADSHEET",
            SPREADSHEET_FORMATS
        )
    ),
    (
        "06_models",
        "Batch 3D Models",
        make_modes(
            "MODEL",
            MODEL_FORMATS
        )
    ),
]
