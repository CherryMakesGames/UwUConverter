import pathlib
import sys
import traceback

import av

import make_key
from audio_converter import convert_audio
from compression import compress_video_lossless, compress_video_by_percent, compress_image_lossless, compress_image_by_percent

from document_converter import convert_document
from file_types import file_types
from image_converter import convert_image
from spreadsheet_converter import convert_spreadsheet
from video_converter import convert_video


av.logging.set_level(av.logging.VERBOSE)


VIDEO_OUTPUTS = {
    "mp4",
    "mkv",
    "mov",
    "avi",
    "webm"
}

AUDIO_OUTPUTS = {
    "mp3",
    "wav",
    "flac",
    "ogg",
    "opus"
}

IMAGE_OUTPUTS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
    "ico",
    "pdf"
}


def ConvertFile(file_path, convert_type):
    action = convert_type.lower()
    input_extension = (
        pathlib.Path(file_path).suffix.lower()
    )

    output_base = file_path.removesuffix(
        pathlib.Path(file_path).suffix
    )

    if action in VIDEO_OUTPUTS:
        convert_video(
            file_path,
            output_base + "." + action,
            action
        )
        return

    if action in AUDIO_OUTPUTS:
        convert_audio(
            file_path,
            output_base + "." + action,
            action
        )
        return

    if (
        action in IMAGE_OUTPUTS
        and input_extension
        in {".png", ".jpg", ".jpeg", ".webp", ".ico", ".raw"}
    ):
        convert_image(
            file_path,
            output_base + "." + action,
            action
        )
        return

        # video compression

    if action == "video_compress_lossless":
        compress_video_lossless(file_path)
        return

    if action == "video_compress_25":
        compress_video_by_percent(
            file_path,
            25
        )
        return

    if action == "video_compress_50":
        compress_video_by_percent(
            file_path,
            50
        )
        return

    if action == "video_compress_75":
        compress_video_by_percent(
            file_path,
            75
        )
        return

    # image compression

    if action == "image_compress_lossless":
        compress_image_lossless(file_path)
        return

    if action == "image_compress_25":
        compress_image_by_percent(
            file_path,
            25
        )
        return

    if action == "image_compress_50":
        compress_image_by_percent(
            file_path,
            50
        )
        return

    if action == "image_compress_75":
        compress_image_by_percent(
            file_path,
            75
        )
        return

    document_actions = {
        "docxfpdf": (
            ".docx",
            "docx_from_pdf"
        ),
        "docpdf": (
            ".pdf",
            "pdf"
        ),
        "doctxt": (
            ".txt",
            "txt"
        ),
        "docodt": (
            ".odt",
            "odt"
        ),
        "docdocx": (
            ".docx",
            "docx"
        )
    }

    if action in document_actions:
        suffix, output_format = (
            document_actions[action]
        )

        convert_document(
            file_path,
            output_base + suffix,
            output_format
        )
        return

    spreadsheet_actions = {
        "sheetpdf": (".pdf", "pdf"),
        "sheetxlsx": (".xlsx", "xlsx"),
        "sheetxls": (".xls", "xls"),
        "sheetods": (".ods", "ods"),
        "sheetcsv": (".csv", "csv"),
        "sheettsv": (".tsv", "tsv")
    }

    if action in spreadsheet_actions:
        suffix, output_format = (
            spreadsheet_actions[action]
        )

        convert_spreadsheet(
            file_path,
            output_base + suffix,
            output_format
        )
        return

    raise ValueError(
        "Unknown conversion type: "
        + convert_type
    )


if __name__ == "__main__":
    is_uninstalling = (
        len(sys.argv) > 1
        and sys.argv[1] == "--uninstall"
    )

    try:
        if is_uninstalling:
            make_key.RemoveExtensions(file_types)

        elif len(sys.argv) > 2:
            ConvertFile(
                sys.argv[1],
                sys.argv[2]
            )

        else:
            make_key.CreateExtensions(file_types)

    except Exception:
        traceback.print_exc()

        if not is_uninstalling:
            input("\nPress Enter to close...")
