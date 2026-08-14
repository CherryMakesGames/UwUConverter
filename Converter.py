import pathlib
import sys
import traceback
from tkinter import messagebox

import av

import platform_menu
from audio_converter import convert_audio
from batch_converter import batch_convert_folder
from batch_dialog import open_batch_dialog
from media_compression import (
    compress_video_lossless,
    compress_video_by_percent,
    compress_image_lossless,
    compress_image_by_percent
)
from document_converter import convert_document
from file_types import file_types
from image_converter import convert_image
from spreadsheet_converter import convert_spreadsheet
from video_converter import convert_video


av.logging.set_level(av.logging.VERBOSE)


VIDEO_OUTPUTS = {
    "mp4", "mkv", "mov", "avi", "webm"
}

AUDIO_OUTPUTS = {
    "mp3", "wav", "flac", "ogg", "opus"
}

IMAGE_OUTPUTS = {
    "png", "jpg", "jpeg", "webp", "ico", "tif", "tiff", "pdf"
}

MODEL_OUTPUTS = {
    "obj", "stl", "ply", "glb"
}



def _menu_contains_action(items, convert_type):
    target = convert_type.lower()

    for _, _, action in items:
        if isinstance(action, list):
            if _menu_contains_action(
                action,
                target
            ):
                return True
            continue

        if str(action).lower() == target:
            return True

    return False


def IsActionSupportedForFile(
    file_path,
    convert_type
):
    action = convert_type.lower()

    # Archive actions are generated separately from file_types.py.
    if action.startswith(
        "archive_extract_"
    ):
        return True

    extension = pathlib.Path(
        file_path
    ).suffix.lower()

    return _menu_contains_action(
        file_types.get(
            extension,
            []
        ),
        action
    )


def ConvertFiles(
    file_paths,
    convert_type
):
    converted = 0
    skipped = 0
    failures = []

    for file_path in file_paths:
        if not IsActionSupportedForFile(
            file_path,
            convert_type
        ):
            skipped += 1
            continue

        try:
            ConvertFile(
                file_path,
                convert_type
            )
            converted += 1

        except Exception as error:
            failures.append(
                (
                    file_path,
                    str(error)
                )
            )

    if failures:
        preview = "\n".join(
            f"- {path}: {error}"
            for path, error
            in failures[:8]
        )

        if len(failures) > 8:
            preview += (
                "\n- ...and "
                + str(
                    len(failures) - 8
                )
                + " more"
            )

        raise RuntimeError(
            "Multi-file conversion finished with errors.\n\n"
            f"Converted: {converted}\n"
            f"Skipped: {skipped}\n"
            f"Failed: {len(failures)}\n\n"
            + preview
        )

    return {
        "converted": converted,
        "skipped": skipped,
        "failed": 0,
    }


def ConvertFile(file_path, convert_type):
    action = convert_type.lower()

    if action == "batch_ui_all":
        open_batch_dialog(file_path)
        return

    if action.startswith("batch_ui_"):
        open_batch_dialog(
            file_path,
            action.removeprefix("batch_ui_")
        )
        return

    if action.startswith("batch_"):
        batch_convert_folder(
            file_path,
            action
        )
        return

    # Windows Explorer can invoke a legacy multi-select verb once for
    # each selected file. The verb itself may have come from another
    # selected file type, e.g. "Convert To JPEG" from a PNG while an
    # OPUS file is also selected.
    #
    # Silently ignore files that do not support the chosen action.
    # This is the same behavior used by ConvertFiles() for mixed
    # selections and prevents unrelated files from reaching the
    # conversion router and raising "Unknown conversion type".
    if not IsActionSupportedForFile(
        file_path,
        convert_type
    ):
        return

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
        and input_extension in {
            ".png", ".jpg", ".jpeg",
            ".webp", ".ico", ".tif", ".tiff", ".raw"
        }
    ):
        convert_image(
            file_path,
            output_base + "." + action,
            action
        )
        return


    model_actions = {
        "modelobj": (".obj", "obj"),
        "modelstl": (".stl", "stl"),
        "modelply": (".ply", "ply"),
        "modelglb": (".glb", "glb"),
    }

    if action in model_actions:
        from model_converter import convert_model

        suffix, output_format = (
            model_actions[action]
        )

        convert_model(
            file_path,
            output_base + suffix,
            output_format
        )
        return


    archive_actions = {
        "archive_extract_here": (False, False),
        "archive_extract_folder": (True, False),
        "archive_extract_here_delete": (False, True),
        "archive_extract_folder_delete": (True, True),
    }

    if action in archive_actions:
        from archive_manager import extract_archive_with_options

        source = pathlib.Path(file_path).expanduser().resolve()
        into_folder, delete_source = archive_actions[action]

        extract_archive_with_options(
            source,
            output_dir=None if into_folder else source.parent,
            delete_source=delete_source,
        )
        return

    video_compression = {
        "video_compress_lossless": None,
        "video_compress_25": 25,
        "video_compress_50": 50,
        "video_compress_75": 75,
    }

    if action in video_compression:
        percent = video_compression[action]

        if percent is None:
            compress_video_lossless(file_path)
        else:
            compress_video_by_percent(
                file_path,
                percent
            )
        return

    image_compression = {
        "image_compress_lossless": None,
        "image_compress_25": 25,
        "image_compress_50": 50,
        "image_compress_75": 75,
    }

    if action in image_compression:
        percent = image_compression[action]

        if percent is None:
            compress_image_lossless(file_path)
        else:
            compress_image_by_percent(
                file_path,
                percent
            )
        return

    document_actions = {
        "docxfpdf": (".docx", "docx_from_pdf"),
        "docpdf": (".pdf", "pdf"),
        "doctxt": (".txt", "txt"),
        "docodt": (".odt", "odt"),
        "docdocx": (".docx", "docx"),
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
        "sheettsv": (".tsv", "tsv"),
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
    if (
        len(sys.argv) > 2
        and sys.argv[1] == "__BATCH_GUI__"
    ):
        open_batch_dialog(sys.argv[2])
        raise SystemExit

    is_uninstalling = (
        len(sys.argv) > 1
        and sys.argv[1] == "--uninstall"
    )

    try:
        if is_uninstalling:
            platform_menu.RemoveExtensions(
                file_types
            )

        elif (
            len(sys.argv) > 3
            and sys.argv[1] == "__MULTI__"
        ):
            ConvertFiles(
                sys.argv[3:],
                sys.argv[2]
            )

        elif len(sys.argv) > 2:
            ConvertFile(
                sys.argv[1],
                sys.argv[2]
            )

        else:
            platform_menu.CreateExtensions(
                file_types
            )

    except Exception:
        error_text = traceback.format_exc()
        traceback.print_exc()

        if not is_uninstalling:
            try:
                messagebox.showerror(
                    "UwUConverter conversion failed",
                    error_text
                )
            except Exception:
                pass
