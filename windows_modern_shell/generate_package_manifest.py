from __future__ import annotations

import os
import pathlib
import re
import runpy
from xml.sax.saxutils import escape


HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
GENERATED = HERE / "generated"

DEFAULT_PUBLISHER = "CN=UwUConverter Shell Extension"
PACKAGE_NAME = "PinkSakuraStudios.UwUConverterShell"
APPLICATION_ID = "UwUConverter"


def four_part_version(value: str) -> str:
    parts = value.strip().split(".")

    if not parts or any(not re.fullmatch(r"\d+", part) for part in parts):
        raise ValueError(f"Invalid APP_VERSION: {value!r}")

    numbers = [int(part) for part in parts]
    numbers = (numbers + [0, 0, 0, 0])[:4]

    if any(number > 65535 for number in numbers):
        raise ValueError("MSIX version components must be <= 65535")

    return ".".join(str(number) for number in numbers)


def render(template_name: str, output_name: str, replacements: dict[str, str]) -> pathlib.Path:
    source = (HERE / template_name).read_text(encoding="utf-8")

    for key, value in replacements.items():
        source = source.replace(key, escape(value, {'"': '&quot;'}))

    output = GENERATED / output_name
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(source, encoding="utf-8")
    return output


def main() -> None:
    version_data = runpy.run_path(str(ROOT / "version.py"))
    app_version = four_part_version(str(version_data["APP_VERSION"]))
    publisher = os.environ.get("UWUCONVERTER_MSIX_PUBLISHER", DEFAULT_PUBLISHER).strip()

    replacements = {
        "@@VERSION@@": app_version,
        "@@PUBLISHER@@": publisher,
        "@@PACKAGE_NAME@@": PACKAGE_NAME,
        "@@APPLICATION_ID@@": APPLICATION_ID,
    }

    package_manifest = render(
        "AppxManifest.xml.in",
        "package/AppxManifest.xml",
        replacements,
    )
    exe_manifest = render(
        "UwUConverter.exe.manifest.in",
        "UwUConverter.exe.manifest",
        replacements,
    )

    print(package_manifest)
    print(exe_manifest)
    print(f"Package version: {app_version}")
    print(f"Publisher: {publisher}")


if __name__ == "__main__":
    main()
