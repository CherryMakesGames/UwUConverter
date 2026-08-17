import base64
import json
import os
import pathlib
import re
import struct
import sys
import tempfile
import urllib.parse
import urllib.request
from email.message import Message

from image_converter import convert_image
from ssl_context import create_verified_ssl_context


HOST_NAME = "com.uwuconverter.browser"
MAX_DOWNLOAD_BYTES = 128 * 1024 * 1024
SUPPORTED_OUTPUTS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
    "ico",
    "tif",
    "tiff",
    "pdf",
}


def _set_binary_stdio():
    if os.name != "nt":
        return

    import msvcrt

    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)


def _read_exact(stream, length):
    data = bytearray()

    while len(data) < length:
        chunk = stream.read(length - len(data))

        if not chunk:
            raise EOFError(
                "Native messaging input ended before the full message arrived."
            )

        data.extend(chunk)

    return bytes(data)


def read_native_message():
    raw_length = sys.stdin.buffer.read(4)

    if not raw_length:
        return None

    if len(raw_length) != 4:
        raise EOFError("Invalid native messaging length header.")

    message_length = struct.unpack("=I", raw_length)[0]

    if message_length > 64 * 1024 * 1024:
        raise ValueError("Native messaging request is too large.")

    payload = _read_exact(
        sys.stdin.buffer,
        message_length,
    )

    return json.loads(
        payload.decode("utf-8")
    )


def write_native_message(message):
    encoded = json.dumps(
        message,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    sys.stdout.buffer.write(
        struct.pack("=I", len(encoded))
    )
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def _linux_downloads_directory():
    config_home = pathlib.Path(
        os.environ.get(
            "XDG_CONFIG_HOME",
            pathlib.Path.home() / ".config",
        )
    )
    user_dirs = config_home / "user-dirs.dirs"

    if user_dirs.is_file():
        try:
            for line in user_dirs.read_text(
                encoding="utf-8",
                errors="ignore",
            ).splitlines():
                if not line.startswith(
                    "XDG_DOWNLOAD_DIR="
                ):
                    continue

                value = line.split("=", 1)[1].strip()

                if (
                    len(value) >= 2
                    and value[0] == value[-1] == '"'
                ):
                    value = value[1:-1]

                value = value.replace(
                    "$HOME",
                    str(pathlib.Path.home()),
                )

                return pathlib.Path(
                    os.path.expandvars(
                        os.path.expanduser(value)
                    )
                )
        except OSError:
            pass

    return pathlib.Path.home() / "Downloads"


def _windows_downloads_directory():
    try:
        import ctypes
        from ctypes import wintypes
        import uuid

        folder_id = uuid.UUID(
            "374DE290-123F-4565-9164-39C4925E467B"
        )
        guid_bytes = folder_id.bytes_le

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", ctypes.c_ubyte * 8),
            ]

        guid = GUID.from_buffer_copy(guid_bytes)
        path_ptr = ctypes.c_wchar_p()

        result = ctypes.windll.shell32.SHGetKnownFolderPath(
            ctypes.byref(guid),
            0,
            None,
            ctypes.byref(path_ptr),
        )

        if result == 0 and path_ptr.value:
            path = pathlib.Path(path_ptr.value)
            ctypes.windll.ole32.CoTaskMemFree(
                path_ptr
            )
            return path

    except Exception:
        pass

    return pathlib.Path.home() / "Downloads"


def get_downloads_directory():
    if os.name == "nt":
        directory = _windows_downloads_directory()
    else:
        directory = _linux_downloads_directory()

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


def _filename_from_content_disposition(value):
    if not value:
        return None

    try:
        message = Message()
        message["content-disposition"] = value
        filename = message.get_filename()

        if filename:
            return filename
    except Exception:
        pass

    return None


def _safe_stem(filename):
    filename = pathlib.Path(
        filename or "image"
    ).name
    stem = pathlib.Path(filename).stem

    stem = re.sub(
        r'[<>:"/\\|?*\x00-\x1f]',
        "_",
        stem,
    )
    stem = stem.strip(" .")

    if not stem:
        return "image"

    return stem[:180]


def _unique_output_path(directory, stem, extension):
    candidate = directory / (
        stem + "." + extension
    )

    if not candidate.exists():
        return candidate

    counter = 1

    while True:
        candidate = directory / (
            f"{stem} ({counter}).{extension}"
        )

        if not candidate.exists():
            return candidate

        counter += 1


def _data_url_bytes(url):
    header, separator, data = url.partition(",")

    if not separator:
        raise ValueError("Invalid data: image URL.")

    metadata = header[5:]
    is_base64 = metadata.lower().endswith(";base64")

    if is_base64:
        raw = base64.b64decode(
            data,
            validate=False,
        )
    else:
        raw = urllib.parse.unquote_to_bytes(data)

    if len(raw) > MAX_DOWNLOAD_BYTES:
        raise ValueError(
            "Image is larger than UwUConverter's 128 MB browser limit."
        )

    return raw, "image"


def _download_http_image(url, page_url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 UwUConverter/0.11 "
            "(+browser native host)"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    }

    if page_url:
        parsed_page = urllib.parse.urlparse(
            page_url
        )

        if parsed_page.scheme in {
            "http",
            "https",
        }:
            headers["Referer"] = page_url

    request = urllib.request.Request(
        url,
        headers=headers,
        method="GET",
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
        context=create_verified_ssl_context(),
    ) as response:
        content_length = response.headers.get(
            "Content-Length"
        )

        if content_length:
            try:
                if int(content_length) > MAX_DOWNLOAD_BYTES:
                    raise ValueError(
                        "Image is larger than UwUConverter's 128 MB browser limit."
                    )
            except ValueError as error:
                if "128 MB" in str(error):
                    raise

        filename = _filename_from_content_disposition(
            response.headers.get(
                "Content-Disposition"
            )
        )

        if not filename:
            parsed = urllib.parse.urlparse(
                response.geturl()
            )
            filename = urllib.parse.unquote(
                pathlib.PurePosixPath(
                    parsed.path
                ).name
            )

        chunks = []
        total = 0

        while True:
            chunk = response.read(
                1024 * 1024
            )

            if not chunk:
                break

            total += len(chunk)

            if total > MAX_DOWNLOAD_BYTES:
                raise ValueError(
                    "Image is larger than UwUConverter's 128 MB browser limit."
                )

            chunks.append(chunk)

        return b"".join(chunks), filename or "image"


def download_image_bytes(url, page_url=None):
    parsed = urllib.parse.urlparse(url)

    if parsed.scheme == "data":
        return _data_url_bytes(url)

    if parsed.scheme == "blob":
        raise ValueError(
            "blob: images are not supported yet. This first version supports normal http(s) and data: images."
        )

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise ValueError(
            "Unsupported image URL scheme: "
            + (parsed.scheme or "unknown")
        )

    return _download_http_image(
        url,
        page_url,
    )


def download_and_convert_image(
    url,
    output_format,
    page_url=None,
):
    output_format = str(
        output_format
    ).lower()

    if output_format not in SUPPORTED_OUTPUTS:
        raise ValueError(
            "Unsupported browser image output format: "
            + output_format
        )

    image_bytes, source_name = download_image_bytes(
        url,
        page_url,
    )

    downloads = get_downloads_directory()
    output_path = _unique_output_path(
        downloads,
        _safe_stem(source_name),
        output_format,
    )

    with tempfile.TemporaryDirectory(
        prefix="uwuconverter-browser-"
    ) as temporary_directory:
        input_path = pathlib.Path(
            temporary_directory
        ) / "source-image"
        input_path.write_bytes(image_bytes)

        convert_image(
            str(input_path),
            str(output_path),
            output_format,
        )

    return output_path


def handle_message(message):
    action = message.get("action")

    if action == "ping":
        return {
            "ok": True,
            "host": HOST_NAME,
        }

    if action != "download_image":
        raise ValueError(
            "Unknown browser host action: "
            + str(action)
        )

    url = message.get("url")
    output_format = message.get("format")

    if not isinstance(url, str) or not url:
        raise ValueError(
            "Browser image URL is missing."
        )

    if not isinstance(
        output_format,
        str,
    ):
        raise ValueError(
            "Browser image output format is missing."
        )

    output_path = download_and_convert_image(
        url,
        output_format,
        page_url=message.get("pageUrl"),
    )

    return {
        "ok": True,
        "path": str(output_path),
        "filename": output_path.name,
    }


def main():
    _set_binary_stdio()

    try:
        message = read_native_message()

        if message is None:
            return

        response = handle_message(message)

    except Exception as error:
        print(
            "UwUConverter browser host error:",
            repr(error),
            file=sys.stderr,
        )
        response = {
            "ok": False,
            "error": str(error),
        }

    write_native_message(response)


if __name__ == "__main__":
    main()
