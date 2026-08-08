import argparse
import pathlib
import sys
import traceback

import av

import platform_menu
from audio_converter import convert_audio
from batch_converter import batch_convert_folder
from compression import (
    compress_image_by_percent,
    compress_image_lossless,
    compress_video_by_percent,
    compress_video_lossless,
    get_output_path,
)
from document_converter import convert_document
from file_types import file_types
from image_converter import convert_image
from spreadsheet_converter import convert_spreadsheet
from video_converter import convert_video


av.logging.set_level(av.logging.ERROR)

VERSION = "0.11-cli"

VIDEO_INPUTS = {".mp4", ".mkv", ".mov", ".avi", ".webm"}
VIDEO_OUTPUTS = {"mp4", "mkv", "mov", "avi", "webm"}

AUDIO_INPUTS = {".mp3", ".wav", ".flac", ".ogg", ".opus"}
AUDIO_OUTPUTS = {"mp3", "wav", "flac", "ogg", "opus"}

IMAGE_INPUTS = {
    ".png", ".jpg", ".jpeg", ".webp", ".ico",
    ".tif", ".tiff", ".raw"
}
IMAGE_OUTPUTS = {
    "png", "jpg", "jpeg", "webp", "ico",
    "tif", "tiff", "pdf"
}

DOCUMENT_INPUTS = {".pdf", ".docx", ".odt", ".txt"}
DOCUMENT_OUTPUTS = {"pdf", "docx", "odt", "txt"}

SPREADSHEET_INPUTS = {
    ".xlsx", ".xls", ".xlsb", ".xlsm",
    ".ods", ".csv", ".tsv"
}
SPREADSHEET_OUTPUTS = {
    "pdf", "xlsx", "xls", "ods", "csv", "tsv"
}

BATCH_OUTPUTS = {
    "image": IMAGE_OUTPUTS,
    "video": VIDEO_OUTPUTS | AUDIO_OUTPUTS,
    "audio": AUDIO_OUTPUTS,
    "document": DOCUMENT_OUTPUTS,
    "spreadsheet": SPREADSHEET_OUTPUTS,
}


def build_parser():
    parser = argparse.ArgumentParser(
        prog="UwUConverter",
        description=(
            "UwUConverter command line interface. "
            "Convert files, compress media, or batch-convert folders "
            "without opening the GUI."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"UwUConverter {VERSION}",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print a full traceback if a command fails.",
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True
    )

    # Convert
    convert = commands.add_parser(
        "convert",
        help="Convert one file."
    )
    convert.add_argument(
        "input",
        help="Input file path."
    )
    convert.add_argument(
        "-t", "--to",
        required=True,
        metavar="FORMAT",
        help="Output format, for example webp, mp4, opus, docx, or csv.",
    )
    convert.add_argument(
        "-o", "--output",
        metavar="PATH",
        help="Exact output path."
    )
    convert.add_argument(
        "--output-dir",
        metavar="DIR",
        help="Put the converted file in this directory."
    )
    convert.add_argument(
        "--suffix",
        default="",
        metavar="TEXT",
        help="Append text to the output filename before the extension."
    )
    convert.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite an existing output file."
    )
    convert.add_argument(
        "--delete-source",
        action="store_true",
        help="Delete the source only after conversion succeeds."
    )

    # Compress
    compress = commands.add_parser(
        "compress",
        help="Compress one image or video."
    )
    compress.add_argument(
        "input",
        help="Input file path."
    )
    compression_mode = compress.add_mutually_exclusive_group(
        required=True
    )
    compression_mode.add_argument(
        "--lossless",
        action="store_true",
        help="Run lossless optimization."
    )
    compression_mode.add_argument(
        "--percent",
        type=int,
        choices=(25, 50, 75),
        help="Target a 25%%, 50%%, or 75%% file-size reduction."
    )
    compress.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite the generated output if it already exists."
    )

    # Batch
    batch = commands.add_parser(
        "batch",
        help="Batch-convert a folder without opening the GUI."
    )
    batch.add_argument(
        "folder",
        help="Folder to process. Direct children only."
    )
    batch.add_argument(
        "-c", "--category",
        required=True,
        choices=sorted(BATCH_OUTPUTS),
        help="File category to process."
    )
    batch.add_argument(
        "-t", "--to",
        required=True,
        metavar="FORMAT",
        help="Output format."
    )
    batch.add_argument(
        "-m", "--mode",
        default="folder",
        choices=("replace", "folder", "beside"),
        help=(
            "Output mode: replace originals, create a sibling output "
            "folder, or place outputs beside originals. Default: folder."
        ),
    )
    batch.add_argument(
        "--log",
        action="store_true",
        help="Create a detailed log in the source folder."
    )
    batch.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Only print the final summary."
    )

    commands.add_parser(
        "formats",
        help="List supported input and output formats."
    )
    commands.add_parser(
        "install-menu",
        help="Install or refresh file-manager integration."
    )
    commands.add_parser(
        "uninstall-menu",
        help="Remove file-manager integration."
    )

    return parser


def normalize_format(value):
    return value.lower().lstrip(".")


def default_output_path(
    input_path,
    output_format,
    output_dir=None,
    suffix=""
):
    extension = "." + output_format

    parent = (
        pathlib.Path(output_dir).expanduser().resolve()
        if output_dir
        else input_path.parent
    )

    filename = input_path.stem + suffix + extension
    output = parent / filename

    if output.resolve() == input_path.resolve():
        output = parent / (
            input_path.stem
            + (suffix or "_converted")
            + extension
        )

    return output


def ensure_output_available(path, force):
    if path.exists() and not force:
        raise FileExistsError(
            f"Output already exists: {path}\n"
            "Use --force to overwrite it."
        )


def convert_command(args):
    source = pathlib.Path(
        args.input
    ).expanduser().resolve()

    if not source.is_file():
        raise FileNotFoundError(
            f"Input file does not exist: {source}"
        )

    output_format = normalize_format(args.to)

    if args.output and args.output_dir:
        raise ValueError(
            "--output and --output-dir cannot be used together."
        )

    if args.output:
        output = pathlib.Path(
            args.output
        ).expanduser().resolve()
    else:
        output = default_output_path(
            source,
            output_format,
            output_dir=args.output_dir,
            suffix=args.suffix,
        )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    ensure_output_available(
        output,
        args.force
    )

    if args.force and output.exists():
        output.unlink()

    extension = source.suffix.lower()

    if extension in VIDEO_INPUTS:
        if output_format in VIDEO_OUTPUTS:
            convert_video(
                str(source),
                str(output),
                output_format
            )
        elif output_format in AUDIO_OUTPUTS:
            convert_audio(
                str(source),
                str(output),
                output_format
            )
        else:
            raise ValueError(
                f"Unsupported output '{output_format}' "
                "for video input."
            )

    elif extension in AUDIO_INPUTS:
        if output_format not in AUDIO_OUTPUTS:
            raise ValueError(
                f"Unsupported output '{output_format}' "
                "for audio input."
            )

        convert_audio(
            str(source),
            str(output),
            output_format
        )

    elif extension in IMAGE_INPUTS:
        if output_format not in IMAGE_OUTPUTS:
            raise ValueError(
                f"Unsupported output '{output_format}' "
                "for image input."
            )

        convert_image(
            str(source),
            str(output),
            output_format
        )

    elif extension in DOCUMENT_INPUTS:
        if output_format not in DOCUMENT_OUTPUTS:
            raise ValueError(
                f"Unsupported output '{output_format}' "
                "for document input."
            )

        document_format = output_format

        if (
            extension == ".pdf"
            and output_format == "docx"
        ):
            document_format = "docx_from_pdf"
        elif extension == ".pdf":
            raise ValueError(
                "PDF input currently only supports DOCX output."
            )

        convert_document(
            str(source),
            str(output),
            document_format
        )

    elif extension in SPREADSHEET_INPUTS:
        if output_format not in SPREADSHEET_OUTPUTS:
            raise ValueError(
                f"Unsupported output '{output_format}' "
                "for spreadsheet input."
            )

        convert_spreadsheet(
            str(source),
            str(output),
            output_format
        )

    else:
        raise ValueError(
            "Unsupported input extension: "
            + (extension or "(none)")
        )

    if (
        args.delete_source
        and source != output
        and output.is_file()
        and output.stat().st_size > 0
    ):
        source.unlink()

    print(output)
    return 0


def compress_command(args):
    source = pathlib.Path(
        args.input
    ).expanduser().resolve()

    if not source.is_file():
        raise FileNotFoundError(
            f"Input file does not exist: {source}"
        )

    extension = source.suffix.lower()

    if extension in VIDEO_INPUTS:
        kind = "video"
    elif extension in {
        ".png", ".jpg", ".jpeg", ".webp"
    }:
        kind = "image"
    else:
        raise ValueError(
            "Compression currently supports "
            "MP4/MKV/MOV/AVI/WEBM and PNG/JPG/JPEG/WEBP."
        )

    suffix = (
        "_lossless"
        if args.lossless
        else f"_compressed_{args.percent}"
    )

    target = pathlib.Path(
        get_output_path(
            str(source),
            suffix
        )
    )

    ensure_output_available(
        target,
        args.force
    )

    if args.force and target.exists():
        target.unlink()

    if kind == "video":
        result = (
            compress_video_lossless(
                str(source)
            )
            if args.lossless
            else compress_video_by_percent(
                str(source),
                args.percent
            )
        )
    else:
        result = (
            compress_image_lossless(
                str(source)
            )
            if args.lossless
            else compress_image_by_percent(
                str(source),
                args.percent
            )
        )

    print(
        pathlib.Path(result).resolve()
    )

    return 0


def batch_progress_printer():
    last_phase = None
    last_processed = -1

    def callback(data):
        nonlocal last_phase, last_processed

        phase = data["phase"]

        if phase == "counting":
            if phase != last_phase:
                print(
                    "Scanning folder...",
                    flush=True
                )

            if (
                data["scanned"]
                and data["scanned"] % 1000 == 0
            ):
                print(
                    f"  {data['scanned']:,} entries checked",
                    flush=True
                )

        elif phase == "converting":
            processed = data["processed"]

            if processed == last_processed:
                return

            last_processed = processed

            print(
                f"[{processed:,}/{data['matched']:,}] "
                f"converted={data['converted']:,} "
                f"skipped={data['skipped']:,} "
                f"failed={data['failed']:,} "
                f"{data['current_file']}",
                flush=True,
            )

        last_phase = phase

    return callback


def batch_command(args):
    output_format = normalize_format(
        args.to
    )

    allowed = BATCH_OUTPUTS[
        args.category
    ]

    if output_format not in allowed:
        raise ValueError(
            f"Unsupported {args.category} batch output "
            f"'{output_format}'. Allowed: "
            + ", ".join(sorted(allowed))
        )

    folder = pathlib.Path(
        args.folder
    ).expanduser().resolve()

    if not folder.is_dir():
        raise NotADirectoryError(
            f"Folder does not exist: {folder}"
        )

    action = (
        f"batch_{args.category}_"
        f"{args.mode}_{output_format}"
    )

    progress = (
        None
        if args.quiet
        else batch_progress_printer()
    )

    stats = batch_convert_folder(
        str(folder),
        action,
        progress_callback=progress,
        create_log=args.log,
    )

    print(
        "Batch complete: "
        f"matched={stats['matched']:,}, "
        f"processed={stats['processed']:,}, "
        f"converted={stats['converted']:,}, "
        f"skipped={stats['skipped']:,}, "
        f"failed={stats['failed']:,}"
    )

    if stats["log_path"]:
        print(
            f"Log: {stats['log_path']}"
        )

    return 2 if stats["failed"] else 0


def formats_command():
    sections = [
        (
            "Video",
            VIDEO_INPUTS,
            VIDEO_OUTPUTS | AUDIO_OUTPUTS
        ),
        (
            "Audio",
            AUDIO_INPUTS,
            AUDIO_OUTPUTS
        ),
        (
            "Images",
            IMAGE_INPUTS,
            IMAGE_OUTPUTS
        ),
        (
            "Documents",
            DOCUMENT_INPUTS,
            DOCUMENT_OUTPUTS
        ),
        (
            "Spreadsheets",
            SPREADSHEET_INPUTS,
            SPREADSHEET_OUTPUTS
        ),
    ]

    for title, inputs, outputs in sections:
        print(title)
        print(
            "  input:  "
            + ", ".join(
                sorted(
                    item.lstrip(".")
                    for item in inputs
                )
            )
        )
        print(
            "  output: "
            + ", ".join(
                sorted(outputs)
            )
        )

    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "convert":
            return convert_command(args)

        if args.command == "compress":
            return compress_command(args)

        if args.command == "batch":
            return batch_command(args)

        if args.command == "formats":
            return formats_command()

        if args.command == "install-menu":
            platform_menu.CreateExtensions(
                file_types
            )
            print(
                "UwUConverter file-manager integration "
                "installed/refreshed."
            )
            return 0

        if args.command == "uninstall-menu":
            platform_menu.RemoveExtensions(
                file_types
            )
            print(
                "UwUConverter file-manager integration removed."
            )
            return 0

        parser.error(
            "Unknown command"
        )

    except KeyboardInterrupt:
        print(
            "Cancelled.",
            file=sys.stderr
        )
        return 130

    except Exception as error:
        if args.debug:
            traceback.print_exc()
        else:
            print(
                f"error: {error}",
                file=sys.stderr
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
