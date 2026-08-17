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

    if not source.is_dir():
        raise FileNotFoundError(
            "Browser extension source folder was not found: "
            + str(source)
        )

    shutil.copytree(source, staging)

    staged_background = staging / "background.js"

    if not staged_background.is_file():
        if COMMON_BACKGROUND.is_file():
            shutil.copy2(
                COMMON_BACKGROUND,
                staged_background,
            )
        else:
            raise FileNotFoundError(
                "Missing background.js for "
                + browser
                + ". Expected either "
                + str(source / "background.js")
                + " or "
                + str(COMMON_BACKGROUND)
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
