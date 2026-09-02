import os
import pathlib
import platform
import tarfile
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from ssl_context import create_verified_ssl_context


CREATE_FORMATS = {
    "7z",
    "zip",
    "tar",
    "gzip",
    "bzip2",
    "xz",
    "wim",
}

CREATE_FORMAT_ALIASES = {
    "gz": "gzip",
    "bz2": "bzip2",
}

SINGLE_FILE_CREATE_FORMATS = {
    "gzip",
    "bzip2",
    "xz",
}

SEVEN_ZIP_WINDOWS_X64_URL = (
    "https://github.com/ip7z/7zip/releases/download/"
    "26.02/7z2602-x64.exe"
)

SEVEN_ZIP_LINUX_URLS = {
    "x86_64": (
        "https://github.com/ip7z/7zip/releases/download/"
        "26.02/7z2602-linux-x64.tar.xz"
    ),
    "arm64": (
        "https://github.com/ip7z/7zip/releases/download/"
        "26.02/7z2602-linux-arm64.tar.xz"
    ),
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



def _clean_subprocess_environment():
    environment = os.environ.copy()

    if sys.platform.startswith("linux"):
        original = environment.get(
            "LD_LIBRARY_PATH_ORIG"
        )

        if original is not None:
            if original:
                environment[
                    "LD_LIBRARY_PATH"
                ] = original
            else:
                environment.pop(
                    "LD_LIBRARY_PATH",
                    None,
                )
        else:
            environment.pop(
                "LD_LIBRARY_PATH",
                None,
            )

        environment.pop(
            "LD_PRELOAD",
            None,
        )

    return environment


def _candidate_7zip_paths():
    candidates = []

    override = os.environ.get("UWUCONVERTER_7ZIP")
    if override:
        candidates.append(pathlib.Path(override))

    if sys.platform.startswith("linux"):
        for command in ("7zz", "7za", "7z"):
            found = shutil.which(command)
            if found:
                candidates.append(
                    pathlib.Path(found)
                )

        candidates.append(
            pathlib.Path.home()
            / ".local/share/UwUConverter/tools/7zip/7zz"
        )
    else:
        for command in ("7z", "7zz", "7za"):
            found = shutil.which(command)
            if found:
                candidates.append(
                    pathlib.Path(found)
                )

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
    found = _find_existing_7zip()

    if found is not None:
        return found

    if os.name == "nt":
        _install_7zip_windows()

        found = _find_existing_7zip()

        if found is not None:
            return found

    if sys.platform.startswith("linux"):
        _install_7zip_linux()

        found = _find_existing_7zip()

        if found is not None:
            return found

    raise FileNotFoundError(
        "7-Zip was not found and automatic installation failed. "
        "Install 7-Zip manually and try again."
    )


def _find_existing_7zip():
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

    return None


def _install_7zip_windows():
    installer_path = (
        pathlib.Path(tempfile.gettempdir())
        / "UwUConverter-7zip-installer.exe"
    )

    try:
        request = urllib.request.Request(
            SEVEN_ZIP_WINDOWS_X64_URL,
            headers={
                "User-Agent": "UwUConverter",
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=60,
            context=create_verified_ssl_context(),
        ) as response:
            with installer_path.open("wb") as output:
                shutil.copyfileobj(
                    response,
                    output,
                )
    except Exception as error:
        raise RuntimeError(
            "Could not download 7-Zip automatically: "
            + str(error)
        ) from error

    if not installer_path.is_file():
        raise RuntimeError(
            "7-Zip installer download did not create a file."
        )

    try:
        result = subprocess.run(
            [
                str(installer_path),
                "/S",
            ],
            check=False,
            env=_clean_subprocess_environment(),
        )

        if result.returncode == 0:
            return

    except OSError:
        pass

    powershell = shutil.which("powershell") or shutil.which("pwsh")

    if not powershell:
        raise RuntimeError(
            "7-Zip needs administrator permission, but PowerShell "
            "was not found to request elevation."
        )

    escaped_path = str(installer_path).replace(
        "'",
        "''",
    )

    command = (
        "Start-Process "
        f"-FilePath '{escaped_path}' "
        "-ArgumentList '/S' "
        "-Verb RunAs "
        "-Wait"
    )

    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-Command",
            command,
        ],
        check=False,
        env=_clean_subprocess_environment(),
    )

    if result.returncode != 0:
        raise RuntimeError(
            "7-Zip automatic installation failed."
        )


def _linux_7zip_architecture():
    machine = platform.machine().lower()

    if machine in {
        "x86_64",
        "amd64",
    }:
        return "x86_64"

    if machine in {
        "aarch64",
        "arm64",
    }:
        return "arm64"

    raise RuntimeError(
        "Automatic 7-Zip installation is not available for "
        + machine
        + "."
    )


def _install_7zip_linux():
    architecture = _linux_7zip_architecture()
    url = SEVEN_ZIP_LINUX_URLS[
        architecture
    ]

    destination = (
        pathlib.Path.home()
        / ".local/share/UwUConverter/tools/7zip"
    )

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    binary = destination / "7zz"

    with tempfile.TemporaryDirectory(
        prefix="UwUConverter-7zip-"
    ) as temp_directory:
        temp_root = pathlib.Path(
            temp_directory
        )
        archive_path = (
            temp_root
            / "7zip.tar.xz"
        )

        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "UwUConverter",
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=60,
                context=create_verified_ssl_context(),
            ) as response:
                with archive_path.open(
                    "wb"
                ) as output:
                    shutil.copyfileobj(
                        response,
                        output,
                    )
        except Exception as error:
            raise RuntimeError(
                "Could not download 7-Zip for Linux automatically: "
                + str(error)
            ) from error

        with tarfile.open(
            archive_path,
            "r:xz",
        ) as archive:
            members = [
                member
                for member in archive.getmembers()
                if pathlib.PurePosixPath(
                    member.name
                ).name
                == "7zz"
                and member.isfile()
            ]

            if not members:
                raise RuntimeError(
                    "The downloaded 7-Zip package does not contain 7zz."
                )

            extracted = archive.extractfile(
                members[0]
            )

            if extracted is None:
                raise RuntimeError(
                    "Could not read 7zz from the downloaded package."
                )

            with binary.open(
                "wb"
            ) as output:
                shutil.copyfileobj(
                    extracted,
                    output,
                )

    binary.chmod(
        binary.stat().st_mode
        | 0o111
    )

    if not binary.is_file():
        raise RuntimeError(
            "7-Zip Linux installation did not create 7zz."
        )


def run_7zip(
    arguments,
    cwd=None,
    capture_output=False,
):
    executable = find_7zip()

    process = subprocess.run(
        [str(executable), *arguments],
        check=False,
        env=_clean_subprocess_environment(),
        cwd=(
            str(cwd)
            if cwd is not None
            else None
        ),
        stdout=(
            subprocess.PIPE
            if capture_output
            else None
        ),
        stderr=(
            subprocess.STDOUT
            if capture_output
            else None
        ),
        text=capture_output,
        errors=(
            "replace"
            if capture_output
            else None
        ),
    )

    if process.returncode != 0:
        error_text = (
            process.stdout.strip()
            if capture_output
            and process.stdout
            else ""
        )

        message = (
            "7-Zip failed with exit code "
            + str(process.returncode)
        )

        if error_text:
            message += (
                "\n\n"
                + error_text
            )

        raise RuntimeError(
            message
        )

    return process


def create_archive(
    archive_path,
    input_paths,
    archive_format=None,
    level=5,
    password=None,
    encrypt_headers=False,
    force=False,
    working_directory=None,
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
    archive_format = CREATE_FORMAT_ALIASES.get(
        archive_format,
        archive_format,
    )

    if archive_format not in CREATE_FORMATS:
        raise ValueError(
            "Archive creation currently supports 7z, zip, tar, gzip, bzip2, xz, and wim."
        )

    if (
        archive_format in SINGLE_FILE_CREATE_FORMATS
        and (
            len(inputs) != 1
            or not inputs[0].is_file()
        )
    ):
        raise ValueError(
            archive_format.upper()
            + " archive creation requires exactly one input file. "
            "Use TAR first when you need to compress multiple files or a folder."
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

    working_path = None

    if working_directory is not None:
        working_path = (
            pathlib.Path(
                working_directory
            )
            .expanduser()
            .resolve()
        )

        if not working_path.is_dir():
            raise NotADirectoryError(
                "Archive working directory does not exist: "
                + str(working_path)
            )

    if working_path is not None:
        input_arguments = []

        for item in inputs:
            try:
                input_arguments.append(
                    str(
                        item.relative_to(
                            working_path
                        )
                    )
                )
            except ValueError:
                input_arguments.append(
                    str(item)
                )

        arguments.extend(
            input_arguments
        )
    else:
        arguments.extend(
            str(item)
            for item in inputs
        )

    run_7zip(
        arguments,
        cwd=working_path,
    )

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
    ).returncode


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

    return run_7zip(
        arguments
    ).returncode




def _validate_archive_for_reading(
    archive_path,
):
    archive = (
        pathlib.Path(
            archive_path
        )
        .expanduser()
        .resolve()
    )

    extension = (
        archive.suffix
        .lower()
        .lstrip(".")
    )

    if (
        extension
        and extension
        not in EXTRACT_FORMATS
    ):
        raise ValueError(
            "Unsupported archive format."
        )

    if not archive.is_file():
        raise FileNotFoundError(
            "Archive does not exist: "
            + str(archive)
        )

    return archive


def _parse_7zip_slt(
    output,
):
    entries = []
    current = {}
    in_entries = False

    for raw_line in output.splitlines():
        line = raw_line.rstrip()

        if line.startswith(
            "----------"
        ):
            in_entries = True
            current = {}
            continue

        if not in_entries:
            continue

        if not line:
            if (
                current
                and current.get("Path")
            ):
                entries.append(
                    current
                )

            current = {}
            continue

        if " = " not in line:
            continue

        key, value = line.split(
            " = ",
            1,
        )

        current[key] = value

    if (
        current
        and current.get("Path")
    ):
        entries.append(
            current
        )

    result = []

    for entry in entries:
        path = (
            entry.get(
                "Path",
                "",
            )
            .replace(
                "\\\\",
                "/",
            )
            .lstrip("/")
        )

        if not path:
            continue

        folder = (
            entry.get("Folder") == "+"
            or entry.get(
                "Attributes",
                "",
            ).startswith("D")
        )

        def number(name):
            try:
                return int(
                    entry.get(
                        name,
                        "0",
                    )
                    or 0
                )
            except ValueError:
                return 0

        result.append(
            {
                "path": path,
                "folder": folder,
                "size": number(
                    "Size"
                ),
                "packed_size": number(
                    "Packed Size"
                ),
                "modified": entry.get(
                    "Modified",
                    "",
                ),
                "crc": entry.get(
                    "CRC",
                    "",
                ),
                "method": entry.get(
                    "Method",
                    "",
                ),
                "encrypted": (
                    entry.get(
                        "Encrypted"
                    )
                    == "+"
                ),
            }
        )

    return result


def list_archive_entries(
    archive_path,
):
    archive = (
        _validate_archive_for_reading(
            archive_path
        )
    )

    process = run_7zip(
        [
            "l",
            "-slt",
            str(archive),
        ],
        capture_output=True,
    )

    return _parse_7zip_slt(
        process.stdout or ""
    )


def extract_archive_entries(
    archive_path,
    entry_paths,
    output_dir,
    password=None,
    overwrite=True,
):
    archive = (
        _validate_archive_for_reading(
            archive_path
        )
    )

    output = (
        pathlib.Path(
            output_dir
        )
        .expanduser()
        .resolve()
    )

    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    entries = [
        str(path)
        for path in entry_paths
        if str(path)
    ]

    if not entries:
        return extract_archive(
            archive,
            output_dir=output,
            password=password,
            overwrite=overwrite,
        )

    arguments = [
        "x",
        str(archive),
        *entries,
        "-o" + str(output),
        "-y" if overwrite else "-aos",
    ]

    if password:
        arguments.append(
            "-p" + password
        )

    run_7zip(
        arguments
    )

    return output


def delete_archive_entries(
    archive_path,
    entry_paths,
):
    archive = (
        _validate_archive_for_reading(
            archive_path
        )
    )

    entries = [
        str(path)
        for path in entry_paths
        if str(path)
    ]

    if not entries:
        return archive

    run_7zip(
        [
            "d",
            str(archive),
            *entries,
            "-y",
        ]
    )

    return archive


def add_to_archive(
    archive_path,
    input_paths,
    working_directory=None,
):
    archive = (
        pathlib.Path(
            archive_path
        )
        .expanduser()
        .resolve()
    )

    inputs = [
        pathlib.Path(path)
        .expanduser()
        .resolve()
        for path in input_paths
    ]

    if not inputs:
        raise ValueError(
            "Select at least one file or folder to add."
        )

    missing = [
        str(path)
        for path in inputs
        if not path.exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Input does not exist: "
            + missing[0]
        )

    archive.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    working_path = None

    if working_directory is not None:
        working_path = (
            pathlib.Path(
                working_directory
            )
            .expanduser()
            .resolve()
        )

    arguments = [
        "a",
        str(archive),
    ]

    if working_path is not None:
        for item in inputs:
            try:
                arguments.append(
                    str(
                        item.relative_to(
                            working_path
                        )
                    )
                )
            except ValueError:
                arguments.append(
                    str(item)
                )
    else:
        arguments.extend(
            str(item)
            for item in inputs
        )

    run_7zip(
        arguments,
        cwd=working_path,
    )

    if not archive.is_file():
        raise RuntimeError(
            "7-Zip did not create or update the archive."
        )

    return archive

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
