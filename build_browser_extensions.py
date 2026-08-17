import pathlib
import shutil
import zipfile


ROOT = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / "browser_extension"
DIST = SOURCE / "dist"
COMMON_BACKGROUND = SOURCE / "background.js"


def build_one(browser):
    source = SOURCE / browser
    staging = DIST / browser

    if staging.exists():
        shutil.rmtree(staging)

    shutil.copytree(source, staging)
    shutil.copy2(
        COMMON_BACKGROUND,
        staging / "background.js",
    )

    output = DIST / (
        "UwUConverter-"
        + browser.capitalize()
        + ".zip"
    )

    if output.exists():
        output.unlink()

    with zipfile.ZipFile(
        output,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as archive:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                archive.write(
                    path,
                    path.relative_to(staging),
                )

    return output


def main():
    DIST.mkdir(
        parents=True,
        exist_ok=True,
    )

    outputs = [
        build_one("chromium"),
        build_one("firefox"),
    ]

    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
