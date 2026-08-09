import os
import pathlib
import time
import traceback
import uuid

CATEGORY_EXTENSIONS = {
    "image": {
        ".png", ".jpg", ".jpeg", ".webp", ".ico",
        ".tif", ".tiff", ".raw"
    },
    "video": {
        ".mp4", ".mkv", ".mov", ".avi", ".webm"
    },
    "audio": {
        ".mp3", ".wav", ".ogg", ".flac", ".opus"
    },
    "document": {
        ".pdf", ".docx", ".odt", ".txt"
    },
    "spreadsheet": {
        ".xlsx", ".xls", ".xlsb", ".xlsm",
        ".ods", ".csv", ".tsv"
    },
    "model": {
        ".obj", ".stl", ".ply", ".glb"
    },
}

OUTPUT_EXTENSIONS = {
    "png": ".png",
    "jpg": ".jpg",
    "jpeg": ".jpeg",
    "webp": ".webp",
    "ico": ".ico",
    "tif": ".tif",
    "tiff": ".tiff",
    "pdf": ".pdf",

    "mp4": ".mp4",
    "mkv": ".mkv",
    "mov": ".mov",
    "avi": ".avi",
    "webm": ".webm",

    "mp3": ".mp3",
    "wav": ".wav",
    "ogg": ".ogg",
    "flac": ".flac",
    "opus": ".opus",

    "docx": ".docx",
    "odt": ".odt",
    "txt": ".txt",

    "xlsx": ".xlsx",
    "xls": ".xls",
    "ods": ".ods",
    "csv": ".csv",
    "tsv": ".tsv",

    "obj": ".obj",
    "stl": ".stl",
    "ply": ".ply",
    "glb": ".glb",
}

BATCH_FORMAT_VERSION = "all-formats-progress-v3"


def parse_batch_action(action):
    parts = action.lower().split("_")

    if len(parts) != 4 or parts[0] != "batch":
        raise ValueError(
            "Invalid batch action: " + action
        )

    _, category, mode, output_format = parts

    if category not in CATEGORY_EXTENSIONS:
        raise ValueError(
            "Unknown batch category: " + category
        )

    if mode not in {"replace", "folder", "beside"}:
        raise ValueError(
            "Unknown batch output mode: " + mode
        )

    if output_format not in OUTPUT_EXTENSIONS:
        raise ValueError(
            "Unknown batch output format: "
            + output_format
        )

    return category, mode, output_format


class NullLog:
    def write(self, value):
        return len(value)

    def flush(self):
        pass

    def __enter__(self):
        return self

    def __exit__(
        self,
        exception_type,
        exception,
        traceback_object
    ):
        return False


def batch_convert_folder(
    folder_path,
    action,
    progress_callback=None,
    cancel_event=None,
    create_log=False
):
    category, mode, output_format = (
        parse_batch_action(action)
    )

    folder = pathlib.Path(folder_path).resolve()

    if not folder.is_dir():
        raise NotADirectoryError(
            f"Not a folder: {folder}"
        )

    output_folder = None

    if mode == "folder":
        output_folder = folder.parent / (
            folder.name
            + " - Converted to "
            + output_format.upper()
        )
        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

    log_path = None

    if create_log:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_path = folder / (
            f"UwUConverter-batch-{timestamp}.log"
        )

    stats = {
        "scanned": 0,
        "matched": 0,
        "processed": 0,
        "converted": 0,
        "skipped": 0,
        "failed": 0,
        "cancelled": False,
        "log_path": (
            str(log_path)
            if log_path is not None
            else None
        ),
    }

    started = time.monotonic()

    def cancelled():
        return (
            cancel_event is not None
            and cancel_event.is_set()
        )

    def report(phase, current_file=""):
        if progress_callback is None:
            return

        progress_callback(
            {
                "phase": phase,
                "scanned": stats["scanned"],
                "matched": stats["matched"],
                "processed": stats["processed"],
                "converted": stats["converted"],
                "skipped": stats["skipped"],
                "failed": stats["failed"],
                "current_file": current_file,
                "elapsed": time.monotonic() - started,
            }
        )

    log_context = (
        log_path.open(
            "w",
            encoding="utf-8",
            buffering=1
        )
        if log_path is not None
        else NullLog()
    )

    with log_context as log:
        log.write("UwUConverter batch conversion\n")
        log.write(f"Folder: {folder}\n")
        log.write(f"Category: {category}\n")
        log.write(f"Mode: {mode}\n")
        log.write(
            f"Output format: {output_format}\n\n"
        )

        report("counting")

        # First pass only counts matching files. It still streams the
        # directory and does not store 100,000 paths in memory.
        with os.scandir(folder) as entries:
            for entry in entries:
                if cancelled():
                    stats["cancelled"] = True
                    break

                stats["scanned"] += 1

                if not entry.is_file(
                    follow_symlinks=False
                ):
                    continue

                extension = pathlib.Path(
                    entry.name
                ).suffix.lower()

                if extension in CATEGORY_EXTENSIONS[category]:
                    stats["matched"] += 1

                if stats["scanned"] % 1000 == 0:
                    report("counting")

        if not stats["cancelled"]:
            stats["scanned"] = 0
            report("converting")

            # Second pass converts one file at a time. Memory use stays
            # stable even for extremely large folders.
            with os.scandir(folder) as entries:
                for entry in entries:
                    if cancelled():
                        stats["cancelled"] = True
                        break

                    stats["scanned"] += 1

                    if not entry.is_file(
                        follow_symlinks=False
                    ):
                        continue

                    source = pathlib.Path(entry.path)

                    if (
                        source.suffix.lower()
                        not in CATEGORY_EXTENSIONS[category]
                    ):
                        continue

                    try:
                        result = convert_one(
                            source,
                            folder,
                            output_folder,
                            category,
                            mode,
                            output_format
                        )

                        if result == "converted":
                            stats["converted"] += 1
                        else:
                            stats["skipped"] += 1
                            log.write(
                                f"SKIPPED\t{source}\t{result}\n"
                            )

                    except Exception as error:
                        stats["failed"] += 1
                        log.write(
                            f"FAILED\t{source}\t"
                            f"{type(error).__name__}: "
                            f"{error}\n"
                        )
                        log.write(
                            traceback.format_exc()
                            + "\n"
                        )

                    stats["processed"] += 1
                    report(
                        "converting",
                        source.name
                    )

        elapsed = time.monotonic() - started

        summary = (
            "\nBatch "
            + (
                "cancelled\n"
                if stats["cancelled"]
                else "complete\n"
            )
            + f"Matched: {stats['matched']:,}\n"
            + f"Processed: {stats['processed']:,}\n"
            + f"Converted: {stats['converted']:,}\n"
            + f"Skipped: {stats['skipped']:,}\n"
            + f"Failed: {stats['failed']:,}\n"
            + f"Elapsed: {elapsed:.1f} seconds\n"
        )

        if log_path is not None:
            summary += f"Log: {log_path}\n"

        log.write(summary)

    report(
        "cancelled"
        if stats["cancelled"]
        else "complete"
    )

    return stats


def convert_one(
    source,
    root_folder,
    output_folder,
    category,
    mode,
    output_format
):
    target_extension = (
        OUTPUT_EXTENSIONS[output_format]
    )

    if mode == "folder":
        final_path = (
            output_folder
            / (source.stem + target_extension)
        )
    else:
        final_path = source.with_suffix(
            target_extension
        )

    source_resolved = source.resolve()
    final_resolved = final_path.resolve()

    if (
        source_resolved == final_resolved
        and mode != "replace"
    ):
        return "source is already in that format"

    if (
        final_path.exists()
        and source_resolved != final_resolved
    ):
        return "output already exists"

    temp_path = make_temp_output(
        final_path
    )

    try:
        dispatch_conversion(
            source,
            temp_path,
            category,
            output_format
        )

        validate_output(temp_path)

        # os.replace is atomic when source and destination are on
        # the same filesystem. Temporary outputs are intentionally
        # created beside their final destination.
        os.replace(
            temp_path,
            final_path
        )

        if (
            mode == "replace"
            and source_resolved != final_resolved
        ):
            source.unlink()

        return "converted"

    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def make_temp_output(final_path):
    token = uuid.uuid4().hex

    return final_path.with_name(
        "."
        + final_path.stem
        + ".uwu-temp-"
        + token
        + final_path.suffix
    )


def validate_output(output_path):
    if not output_path.is_file():
        raise RuntimeError(
            "Converter did not create an output file"
        )

    if output_path.stat().st_size <= 0:
        raise RuntimeError(
            "Converter created an empty output file"
        )


def dispatch_conversion(
    source,
    output_path,
    category,
    output_format
):
    source_string = str(source)
    output_string = str(output_path)

    if category == "image":
        from image_converter import convert_image

        convert_image(
            source_string,
            output_string,
            output_format
        )
        return

    if category == "video":
        if output_format in {
            "mp3",
            "wav",
            "ogg",
            "flac",
            "opus"
        }:
            from audio_converter import convert_audio

            convert_audio(
                source_string,
                output_string,
                output_format
            )
        else:
            from video_converter import convert_video

            convert_video(
                source_string,
                output_string,
                output_format
            )
        return

    if category == "audio":
        from audio_converter import convert_audio

        convert_audio(
            source_string,
            output_string,
            output_format
        )
        return

    if category == "document":
        from document_converter import convert_document

        document_format = output_format

        if (
            source.suffix.lower() == ".pdf"
            and output_format == "docx"
        ):
            document_format = "docx_from_pdf"

        convert_document(
            source_string,
            output_string,
            document_format
        )
        return

    if category == "spreadsheet":
        from spreadsheet_converter import convert_spreadsheet

        convert_spreadsheet(
            source_string,
            output_string,
            output_format
        )
        return

    if category == "model":
        from model_converter import convert_model

        convert_model(
            source_string,
            output_string,
            output_format
        )
        return

    raise ValueError(
        "Unsupported batch category: "
        + category
    )
