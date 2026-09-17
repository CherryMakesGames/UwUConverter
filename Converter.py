import pathlib
import sys
import traceback
from tkinter import messagebox

import av

from archive_progress_ui import (
    show_create_archive_progress,
    show_extract_archives_progress,
)
from archive_ui import open_archive_manager
from audio_converter import convert_audio
from conflict_dialog import (
    CANCEL,
    KEEP_BOTH,
    REPLACE,
    SKIP,
    ConflictResolver,
    unique_output_path,
)
from batch_converter import batch_convert_folder
from batch_dialog import open_batch_dialog
from media_compression import (
    compress_video_lossless,
    compress_video_by_percent,
    compress_image_lossless,
    compress_image_by_percent,
    get_output_path,
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
    if (
        action == "archive_open_ui"
        or action.startswith(
            "archive_extract_"
        )
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


def CreateZipFromSelection(
    file_paths,
):
    from tkinter import filedialog

    inputs = [
        pathlib.Path(path)
        .expanduser()
        .resolve()
        for path in file_paths
    ]

    if not inputs:
        raise ValueError(
            "Select at least one file or folder to compress."
        )

    missing = [
        str(path)
        for path in inputs
        if not path.exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Selected item no longer exists: "
            + missing[0]
        )

    first_parent = inputs[0].parent
    same_parent = all(
        path.parent == first_parent
        for path in inputs
    )

    if len(inputs) == 1:
        default_name = (
            inputs[0].name
            + ".zip"
        )
    else:
        default_name = "Archive.zip"

    output_text = filedialog.asksaveasfilename(
        title="Compress selection to ZIP",
        initialdir=str(first_parent),
        initialfile=default_name,
        defaultextension=".zip",
        filetypes=[
            (
                "ZIP archive",
                "*.zip",
            ),
        ],
    )

    if not output_text:
        return None

    output = (
        pathlib.Path(output_text)
        .expanduser()
        .resolve()
    )

    if output.suffix.lower() != ".zip":
        output = pathlib.Path(
            str(output)
            + ".zip"
        )

    if output in inputs:
        raise ValueError(
            "The ZIP output cannot overwrite one of the selected inputs."
        )

    replace_existing = False

    if output.exists():
        resolver = ConflictResolver()
        decision = resolver.resolve(
            inputs[0],
            output,
        )

        if decision == SKIP:
            return None

        if decision == CANCEL:
            return None

        if decision == KEEP_BOTH:
            output = unique_output_path(
                output
            )

        elif decision == REPLACE:
            replace_existing = True

        else:
            raise ValueError(
                "Unknown conflict decision: "
                + str(decision)
            )

    success = show_create_archive_progress(
        output,
        inputs,
        archive_format="zip",
        level=5,
        force=replace_existing,
        working_directory=(
            first_parent
            if same_parent
            else None
        ),
    )

    return (
        output
        if success
        else None
    )


def ResolveOutputConflict(
    source_path,
    output_path,
    conflict_resolver=None,
):
    source = pathlib.Path(
        source_path
    ).expanduser().resolve()

    output = pathlib.Path(
        output_path
    ).expanduser().resolve()

    if (
        source == output
        or not output.exists()
    ):
        return output

    resolver = (
        conflict_resolver
        if conflict_resolver is not None
        else ConflictResolver()
    )

    decision = resolver.resolve(
        source,
        output,
    )

    if decision == REPLACE:
        return output

    if decision == KEEP_BOTH:
        return unique_output_path(
            output
        )

    if decision == SKIP:
        return None

    if decision == CANCEL:
        return CANCEL

    raise ValueError(
        "Unknown conflict decision: "
        + str(decision)
    )


def ConvertFiles(
    file_paths,
    convert_type
):
    action = convert_type.lower()

    if action.startswith(
        "archive_extract_"
    ):
        archives = [
            file_path
            for file_path in file_paths
            if IsActionSupportedForFile(
                file_path,
                action
            )
        ]

        if archives:
            success = (
                show_extract_archives_progress(
                    archives,
                    action,
                )
            )

            return {
                "converted": (
                    len(archives)
                    if success
                    else 0
                ),
                "skipped": (
                    len(file_paths)
                    - len(archives)
                ),
                "failed": (
                    0
                    if success
                    else len(archives)
                ),
            }

    converted = 0
    skipped = 0
    failures = []
    resolver = ConflictResolver()

    for file_path in file_paths:
        if not IsActionSupportedForFile(
            file_path,
            convert_type
        ):
            skipped += 1
            continue

        try:
            result = ConvertFile(
                file_path,
                convert_type,
                conflict_resolver=resolver,
            )

            if result == "skipped":
                skipped += 1

            elif result == "cancelled":
                break

            else:
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


def ConvertFile(
    file_path,
    convert_type,
    conflict_resolver=None,
):
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

    input_extension = (
        pathlib.Path(file_path).suffix.lower()
    )

    output_base = file_path.removesuffix(
        pathlib.Path(file_path).suffix
    )

    if action in VIDEO_OUTPUTS:
        output_path = ResolveOutputConflict(
            file_path,
            output_base + "." + action,
            conflict_resolver,
        )

        if output_path is None:
            return "skipped"

        if output_path == CANCEL:
            return "cancelled"

        convert_video(
            file_path,
            str(output_path),
            action
        )
        return "converted"

    if action in AUDIO_OUTPUTS:
        output_path = ResolveOutputConflict(
            file_path,
            output_base + "." + action,
            conflict_resolver,
        )

        if output_path is None:
            return "skipped"

        if output_path == CANCEL:
            return "cancelled"

        convert_audio(
            file_path,
            str(output_path),
            action
        )
        return "converted"

    if (
        action in IMAGE_OUTPUTS
        and input_extension in {
            ".png", ".jpg", ".jpeg",
            ".webp", ".ico", ".tif", ".tiff", ".raw"
        }
    ):
        output_path = ResolveOutputConflict(
            file_path,
            output_base + "." + action,
            conflict_resolver,
        )

        if output_path is None:
            return "skipped"

        if output_path == CANCEL:
            return "cancelled"

        convert_image(
            file_path,
            str(output_path),
            action
        )
        return "converted"


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

        output_path = ResolveOutputConflict(
            file_path,
            output_base + suffix,
            conflict_resolver,
        )

        if output_path is None:
            return "skipped"

        if output_path == CANCEL:
            return "cancelled"

        convert_model(
            file_path,
            str(output_path),
            output_format
        )
        return "converted"


    if action == "archive_open_ui":
        open_archive_manager(
            file_path
        )
        return


    archive_actions = {
        "archive_extract_here",
        "archive_extract_folder",
        "archive_extract_here_delete",
        "archive_extract_folder_delete",
    }

    if action in archive_actions:
        show_extract_archives_progress(
            [
                file_path
            ],
            action,
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

        suffix = (
            "_lossless"
            if percent is None
            else "_compressed_"
            + str(percent)
        )

        output_path = ResolveOutputConflict(
            file_path,
            get_output_path(
                file_path,
                suffix,
            ),
            conflict_resolver,
        )

        if output_path is None:
            return "skipped"

        if output_path == CANCEL:
            return "cancelled"

        if percent is None:
            compress_video_lossless(
                file_path,
                output_file_path=str(
                    output_path
                ),
            )
        else:
            compress_video_by_percent(
                file_path,
                percent,
                output_file_path=str(
                    output_path
                ),
            )

        return "converted"

    image_compression = {
        "image_compress_lossless": None,
        "image_compress_25": 25,
        "image_compress_50": 50,
        "image_compress_75": 75,
    }

    if action in image_compression:
        percent = image_compression[action]

        suffix = (
            "_lossless"
            if percent is None
            else "_compressed_"
            + str(percent)
        )

        output_path = ResolveOutputConflict(
            file_path,
            get_output_path(
                file_path,
                suffix,
            ),
            conflict_resolver,
        )

        if output_path is None:
            return "skipped"

        if output_path == CANCEL:
            return "cancelled"

        if percent is None:
            compress_image_lossless(
                file_path,
                output_file_path=str(
                    output_path
                ),
            )
        else:
            compress_image_by_percent(
                file_path,
                percent,
                output_file_path=str(
                    output_path
                ),
            )

        return "converted"

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
        output_path = ResolveOutputConflict(
            file_path,
            output_base + suffix,
            conflict_resolver,
        )

        if output_path is None:
            return "skipped"

        if output_path == CANCEL:
            return "cancelled"

        convert_document(
            file_path,
            str(output_path),
            output_format
        )
        return "converted"

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
        output_path = ResolveOutputConflict(
            file_path,
            output_base + suffix,
            conflict_resolver,
        )

        if output_path is None:
            return "skipped"

        if output_path == CANCEL:
            return "cancelled"

        convert_spreadsheet(
            file_path,
            str(output_path),
            output_format
        )
        return "converted"

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

    is_setting_up_integrations = (
        len(sys.argv) > 1
        and sys.argv[1] == "--setup-integrations"
    )

    try:
        if is_uninstalling:
            import platform_menu

            platform_menu.RemoveExtensions(
                file_types
            )

        elif is_setting_up_integrations:
            import platform_menu

            platform_menu.CreateExtensions(
                file_types
            )

        elif (
            len(sys.argv) > 3
            and sys.argv[1] == "__MULTI__"
        ):
            if (
                sys.argv[2].lower()
                == "archive_create_zip_prompt"
            ):
                CreateZipFromSelection(
                    sys.argv[3:]
                )
            else:
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
            # Opening the executable without an operation must not mutate
            # Explorer/browser integration. Integration setup is installer-only.
            raise SystemExit

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
