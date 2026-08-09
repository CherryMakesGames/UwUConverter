import os
import pathlib
import shutil
import subprocess
import sys


CREATE_FORMATS = {
    "7z",
    "zip",
    "tar",
    "gzip",
    "gz",
    "bzip2",
    "bz2",
    "xz",
    "wim",
}

EXTRACT_FORMATS = {
    "7z",
    "zip",
    "rar",
    "tar",
    "gzip",
    "gz",
    "bzip2",
    "bz2",
    "xz",
    "wim",
    "cab",
    "iso",
    "arj",
    "lzh",
    "lzma",
    "rpm",
    "dmg",
    "xar",
}


def _candidate_7zip_paths():
    candidates = []

    override = os.environ.get("UWUCONVERTER_7ZIP")
    if override:
        candidates.append(pathlib.Path(override))

    # Installed command names.
    for command in ("7z", "7zz", "7za"):
        found = shutil.which(command)
        if found:
            candidates.append(pathlib.Path(found))

    if os.name == "nt":
        for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
            root = os.environ.get(env_name)
            if root:
                candidates.append(
                    pathlib.Path(root) / "7-Zip" / "7z.exe"
                )

        # In case UwUConverter later ships its own private 7-Zip copy.
        executable = pathlib.Path(sys.executable).resolve()
        candidates.extend(
            [
                executable.parent / "tools" / "7zip" / "7z.exe",
                executable.parent.parent / "tools" / "7zip" / "7z.exe",
                executable.parent.parent / "tools" / "7zip" / "7za.exe",
            ]
        )

    return candidates


def find_7zip():
    seen = set()

    for candidate in _candidate_7zip_paths():
        try:
            resolved = candidate.expanduser().resolve()
        except OSError:
            continue

        key = str(resolved).lower()

        if key in seen:
            continue

        seen.add(key)

        if resolved.is_file():
            return resolved

    raise FileNotFoundError(
        "7-Zip was not found. Re-run the UwUConverter installer "
        "or install 7-Zip manually."
    )


def run_7zip(arguments):
    executable = find_7zip()

    process = subprocess.run(
        [str(executable), *arguments],
        check=False,
    )

    if process.returncode != 0:
        raise RuntimeError(
            "7-Zip failed with exit code "
            + str(process.returncode)
        )

    return process.returncode


def create_archive(
    archive_path,
    input_paths,
    archive_format=None,
    level=5,
    password=None,
    encrypt_headers=False,
    force=False,
):
    archive = pathlib.Path(archive_path).expanduser().resolve()

    if not input_paths:
        raise ValueError("At least one input file or folder is required.")

    inputs = [
        pathlib.Path(item).expanduser().resolve()
        for item in input_paths
    ]

    missing = [
        str(item)
        for item in inputs
        if not item.exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Input does not exist: " + missing[0]
        )

    if archive_format is None:
        archive_format = archive.suffix.lower().lstrip(".") or "7z"

    archive_format = archive_format.lower()

    if archive_format not in CREATE_FORMATS:
        raise ValueError(
            "Archive creation currently supports 7z, zip, tar, "
            "gzip, bzip2, xz, and wim."
        )

    if not 0 <= level <= 9:
        raise ValueError("Compression level must be from 0 to 9.")

    if archive.exists():
        if not force:
            raise FileExistsError(
                f"Archive already exists: {archive}\n"
                "Use --force to replace it."
            )

        archive.unlink()

    archive.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    arguments = [
        "a",
        f"-t{archive_format}",
        f"-mx={level}",
        str(archive),
    ]

    if password:
        arguments.append("-p" + password)

        if encrypt_headers and archive_format == "7z":
            arguments.append("-mhe=on")

    arguments.extend(str(item) for item in inputs)

    run_7zip(arguments)

    if not archive.is_file() or archive.stat().st_size <= 0:
        raise RuntimeError("7-Zip did not create a valid archive.")

    return archive


def extract_archive(
    archive_path,
    output_dir=None,
    password=None,
    overwrite=True,
):
    archive = pathlib.Path(archive_path).expanduser().resolve()

    extension = archive.suffix.lower().lstrip(".")
    if extension and extension not in EXTRACT_FORMATS:
        raise ValueError(
            "Unsupported archive format for extraction."
        )

    if not archive.is_file():
        raise FileNotFoundError(
            f"Archive does not exist: {archive}"
        )

    if output_dir is None:
        output = archive.parent / archive.stem
    else:
        output = pathlib.Path(output_dir).expanduser().resolve()

    output.mkdir(
        parents=True,
        exist_ok=True
    )

    arguments = [
        "x",
        str(archive),
        "-o" + str(output),
        "-y" if overwrite else "-aos",
    ]

    if password:
        arguments.append("-p" + password)

    run_7zip(arguments)
    return output


def list_archive(archive_path):
    archive = pathlib.Path(archive_path).expanduser().resolve()

    extension = archive.suffix.lower().lstrip(".")
    if extension and extension not in EXTRACT_FORMATS:
        raise ValueError(
            "Unsupported archive format for listing."
        )

    if not archive.is_file():
        raise FileNotFoundError(
            f"Archive does not exist: {archive}"
        )

    return run_7zip(
        ["l", str(archive)]
    )


def test_archive(archive_path, password=None):
    archive = pathlib.Path(archive_path).expanduser().resolve()

    extension = archive.suffix.lower().lstrip(".")
    if extension and extension not in EXTRACT_FORMATS:
        raise ValueError(
            "Unsupported archive format for testing."
        )

    if not archive.is_file():
        raise FileNotFoundError(
            f"Archive does not exist: {archive}"
        )

    arguments = ["t", str(archive)]

    if password:
        arguments.append("-p" + password)

    return run_7zip(arguments)


def extract_archive_with_options(
    archive_path,
    output_dir=None,
    password=None,
    overwrite=True,
    delete_source=False,
):
    archive = pathlib.Path(
        archive_path
    ).expanduser().resolve()

    output = extract_archive(
        archive,
        output_dir=output_dir,
        password=password,
        overwrite=overwrite,
    )

    if delete_source:
        archive.unlink()

    return output
