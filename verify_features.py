#!/usr/bin/env python3
import contextlib
import importlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import traceback

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

RESULTS = []


def record(name, status, detail=""):
    RESULTS.append((name, status, detail))
    print(f"{status:4}  {name}" + (f" - {detail}" if detail else ""))


def check(name, func):
    try:
        detail = func()
        record(name, "PASS", detail or "")
    except SkipTest as error:
        record(name, "SKIP", str(error))
    except Exception as error:
        record(name, "FAIL", f"{type(error).__name__}: {error}")
        traceback.print_exc()


class SkipTest(Exception):
    pass


def require_module(name):
    try:
        return importlib.import_module(name)
    except Exception as error:
        raise SkipTest(f"missing/unusable dependency {name}: {error}") from error


def test_python_syntax():
    import py_compile

    count = 0
    for path in ROOT.glob("*.py"):
        py_compile.compile(str(path), doraise=True)
        count += 1
    return f"{count} Python files"


def test_shell_syntax():
    scripts = [
        ROOT / "build_linux.sh",
        ROOT / "install_linux.sh",
        ROOT / "uninstall_linux.sh",
    ]
    for path in scripts:
        result = subprocess.run(
            ["bash", "-n", str(path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
    return "Linux scripts parse with bash -n"


def test_cli_parser():
    import cli

    parser = cli.build_parser()
    examples = [
        ["convert", "image.png", "--to", "webp"],
        ["compress", "image.png", "--percent", "40"],
        ["batch", ".", "-c", "image", "-t", "webp", "-m", "folder"],
        ["batch", ".", "-c", "model", "-t", "glb", "-m", "beside"],
        ["archive", "create", "archive.tar", "a.txt", "--type", "tar"],
        ["archive", "create", "archive.xz", "a.txt", "--type", "xz"],
        ["archive", "create", "archive.gz", "a.txt", "--type", "gz"],
        ["archive", "create", "archive.bz2", "a.txt", "--type", "bz2"],
        ["archive", "extract", "archive.rar", "--here", "--delete-source"],
        ["archive", "extract", "archive.zip", "-o", "output"],
        ["archive", "list", "archive.7z"],
        ["archive", "test", "archive.rar"],
        ["update", "--check-only"],
        ["formats"],
        ["install-menu"],
        ["uninstall-menu"],
    ]
    for argv in examples:
        parser.parse_args(argv)
    return f"{len(examples)} command forms"


def test_cli_formats_output():
    import cli
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = cli.formats_command()
    output = buffer.getvalue()
    for expected in ["Video", "Audio", "Images", "Documents", "Spreadsheets", "3D Models"]:
        if expected not in output:
            raise AssertionError(f"missing {expected}")
    if code != 0:
        raise AssertionError(f"unexpected exit {code}")
    return "all converter categories listed"


def test_updater_logic():
    import updater

    if not updater.is_newer_version("v0.12", "0.11"):
        raise AssertionError("version comparison failed")
    if updater.is_newer_version("v0.10", "0.11"):
        raise AssertionError("downgrade considered newer")

    release = {
        "assets": [
            {"name": "UwUConverter-Setup.exe"},
            {"name": "UwUConverter-linux-x86_64.tar.gz"},
            {"name": "UwUConverter-linux-arm64.tar.gz"},
        ]
    }
    if updater.select_windows_installer(release)["name"] != "UwUConverter-Setup.exe":
        raise AssertionError("Windows asset selection failed")

    selected = updater.select_linux_package(release)
    if selected is None or "linux" not in selected["name"].lower():
        raise AssertionError("Linux asset selection failed")

    return "version comparison + platform asset selection"


def test_updater_linux_package_extract():
    import updater

    with tempfile.TemporaryDirectory() as temp:
        temp = pathlib.Path(temp)
        package_root = temp / "package" / "UwUConverterGUI"
        package_root.mkdir(parents=True)
        installer = package_root / "install.sh"
        installer.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        installer.chmod(0o755)
        package = temp / "UwUConverter-linux-x86_64.tar.gz"
        with tarfile.open(package, "w:gz") as archive:
            archive.add(temp / "package", arcname="payload")

        extracted_root, extracted_installer = updater.extract_linux_package(package)
        try:
            if not extracted_installer.is_file():
                raise AssertionError("install.sh not found after extraction")
        finally:
            shutil.rmtree(extracted_root, ignore_errors=True)
    return "tar.gz package safely locates install.sh"


def test_linux_autostart_install_script():
    text = (ROOT / "install_linux.sh").read_text(encoding="utf-8")
    required = [
        "uwuconverter-updater.desktop",
        "UwUConverterUpdater",
        "--auto",
        "--update",
    ]
    for item in required:
        if item not in text:
            raise AssertionError(f"install script missing {item}")
    build = (ROOT / "build_linux.sh").read_text(encoding="utf-8")
    for item in [
        "UwUConverterUpdater",
        "UwUConverter-linux-${RELEASE_ARCH}.tar.gz",
        ".venv/bin/python",
    ]:
        if item not in build:
            raise AssertionError(f"build script missing {item}")
    return "build package + XDG autostart wiring present"


def test_linux_install_uninstall_runtime():
    with tempfile.TemporaryDirectory() as temp:
        temp = pathlib.Path(temp)
        package = temp / "package"
        home = temp / "home"
        (package / "cli").mkdir(parents=True)
        home.mkdir()

        shutil.copy2(ROOT / "install_linux.sh", package / "install.sh")
        shutil.copy2(ROOT / "uninstall_linux.sh", package / "uninstall.sh")

        for name in ["UwUConverterGUI", "UwUConverterBatch", "UwUConverterUpdater"]:
            path = package / name
            path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            path.chmod(0o755)

        cli = package / "cli" / "UwUConverter"
        cli.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        cli.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(home)
        env["XDG_DATA_HOME"] = str(home / ".local/share")
        env["XDG_CONFIG_HOME"] = str(home / ".config")
        env["XDG_STATE_HOME"] = str(home / ".local/state")

        result = subprocess.run(
            ["bash", str(package / "install.sh"), "--update"],
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stdout + result.stderr)

        app = home / ".local/share/UwUConverter"
        link = home / ".local/bin/UwUConverter"
        autostart = home / ".config/autostart/uwuconverter-updater.desktop"

        if not app.is_dir() or not link.is_symlink() or not autostart.is_file():
            raise AssertionError("Linux install did not create app/CLI/autostart")

        result = subprocess.run(
            ["bash", str(app / "uninstall.sh")],
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stdout + result.stderr)

        if app.exists() or link.exists() or autostart.exists():
            raise AssertionError("Linux uninstall left installed files behind")

    return "actual temp HOME install + uninstall"


def test_linux_menu_generation():
    with tempfile.TemporaryDirectory() as home:
        code = textwrap.dedent(
            f"""
            import pathlib, sys
            sys.path.insert(0, {str(ROOT)!r})
            import linux_menu
            from file_types import file_types
            linux_menu.CreateExtensions(file_types)
            root = pathlib.Path.home() / '.local/share/kio/servicemenus'
            archive = root / 'uwuconverter-archive-extract.desktop'
            assert archive.is_file(), archive
            txt = archive.read_text()
            for label in [
                'Extract Here',
                'Extract to Archive-Named Folder',
                'Extract Here and Delete Archive',
                'Extract to Archive-Named Folder and Delete Archive',
            ]:
                assert label in txt, label
            files = list(root.glob('uwuconverter-file-*.desktop'))
            names = [p.name for p in files]
            assert len(names) == len(set(names))
            assert files
            """
        )
        env = os.environ.copy()
        env["HOME"] = home
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError((result.stdout + result.stderr).strip())
    return "Dolphin file, folder, archive menus generated without duplicate files"


def test_batch_engine():
    import batch_converter

    original_dispatch = batch_converter.dispatch_conversion

    def fake_dispatch(source, output_path, category, output_format):
        pathlib.Path(output_path).write_bytes(b"converted:" + pathlib.Path(source).name.encode())

    batch_converter.dispatch_conversion = fake_dispatch
    try:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)

            folder = root / "folder_mode"
            folder.mkdir()
            (folder / "a.png").write_bytes(b"a")
            (folder / "b.jpg").write_bytes(b"b")
            stats = batch_converter.batch_convert_folder(
                folder,
                "batch_image_folder_webp",
                create_log=True,
            )
            if stats["converted"] != 2 or stats["failed"] != 0:
                raise AssertionError(stats)
            output = root / "folder_mode - Converted to WEBP"
            if not (output / "a.webp").is_file() or not (output / "b.webp").is_file():
                raise AssertionError("folder mode output missing")
            if not stats["log_path"] or not pathlib.Path(stats["log_path"]).is_file():
                raise AssertionError("batch log missing")

            beside = root / "beside"
            beside.mkdir()
            (beside / "c.jpg").write_bytes(b"c")
            stats = batch_converter.batch_convert_folder(
                beside,
                "batch_image_beside_png",
            )
            if stats["converted"] != 1 or not (beside / "c.png").is_file():
                raise AssertionError("beside mode failed")

            replace = root / "replace"
            replace.mkdir()
            source = replace / "d.jpg"
            source.write_bytes(b"d")
            stats = batch_converter.batch_convert_folder(
                replace,
                "batch_image_replace_png",
            )
            if stats["converted"] != 1 or source.exists() or not (replace / "d.png").is_file():
                raise AssertionError("replace mode failed")
    finally:
        batch_converter.dispatch_conversion = original_dispatch
    return "folder/beside/replace/log safety paths"


def test_image_conversion():
    require_module("PIL")
    from PIL import Image
    import image_converter

    with tempfile.TemporaryDirectory() as temp:
        temp = pathlib.Path(temp)
        source = temp / "source.png"
        Image.new("RGBA", (64, 64), (255, 0, 0, 128)).save(source)
        for fmt in ["jpg", "jpeg", "webp", "ico", "tif", "tiff", "pdf"]:
            target = temp / f"out.{fmt}"
            image_converter.convert_image(source, target, fmt)
            if not target.is_file() or target.stat().st_size <= 0:
                raise AssertionError(f"{fmt} output missing")
    return "PNG -> JPG/JPEG/WEBP/ICO/TIF/TIFF/PDF"


def test_image_compression():
    require_module("PIL")
    from PIL import Image
    import media_compression

    with tempfile.TemporaryDirectory() as temp:
        temp = pathlib.Path(temp)
        source = temp / "source.png"
        Image.new("RGB", (256, 256), (100, 150, 200)).save(source)

        lossless = pathlib.Path(
            media_compression.compress_image_lossless(
                source
            )
        )
        percent = pathlib.Path(
            media_compression.compress_image_by_percent(
                source,
                40,
            )
        )

        for output in [lossless, percent]:
            if not output.is_file() or output.stat().st_size <= 0:
                raise AssertionError("image compression output missing")

    return "lossless + arbitrary percentage image compression"


def test_document_conversion():
    require_module("docx")
    require_module("odf")
    require_module("reportlab")
    import document_converter

    with tempfile.TemporaryDirectory() as temp:
        temp = pathlib.Path(temp)
        source = temp / "source.txt"
        source.write_text("hello\nworld", encoding="utf-8")
        outputs = {}
        for fmt in ["docx", "odt", "pdf"]:
            target = temp / f"out.{fmt}"
            document_converter.convert_document(source, target, fmt)
            if not target.is_file() or target.stat().st_size <= 0:
                raise AssertionError(f"{fmt} output missing")
            outputs[fmt] = target

        for input_fmt in ["docx", "odt"]:
            target = temp / f"roundtrip-{input_fmt}.txt"
            document_converter.convert_document(outputs[input_fmt], target, "txt")
            if "hello" not in target.read_text(encoding="utf-8"):
                raise AssertionError(f"{input_fmt} roundtrip failed")

        # PDF -> DOCX is separately optional because pdf2docx is a heavy dependency.
        try:
            importlib.import_module("pdf2docx")
        except Exception:
            return "TXT/DOCX/ODT/PDF paths; PDF->DOCX skipped (pdf2docx unavailable)"
        target = temp / "from-pdf.docx"
        document_converter.convert_document(outputs["pdf"], target, "docx_from_pdf")
        if not target.is_file() or target.stat().st_size <= 0:
            raise AssertionError("PDF->DOCX output missing")
    return "TXT/DOCX/ODT/PDF including PDF->DOCX"


def test_spreadsheet_conversion():
    require_module("pandas")
    require_module("openpyxl")
    require_module("odf")
    require_module("reportlab")
    import spreadsheet_converter

    with tempfile.TemporaryDirectory() as temp:
        temp = pathlib.Path(temp)
        source = temp / "source.csv"
        source.write_text("name,value\na,1\nb,2\n", encoding="utf-8")
        targets = {}
        for fmt in ["xlsx", "ods", "tsv", "pdf"]:
            target = temp / f"out.{fmt}"
            spreadsheet_converter.convert_spreadsheet(source, target, fmt)
            if not target.is_file() or target.stat().st_size <= 0:
                raise AssertionError(f"{fmt} output missing")
            targets[fmt] = target

        back = temp / "back.csv"
        spreadsheet_converter.convert_spreadsheet(targets["xlsx"], back, "csv")
        if "name" not in back.read_text(encoding="utf-8"):
            raise AssertionError("XLSX -> CSV failed")

        try:
            importlib.import_module("xlwt")
        except Exception:
            return "CSV/XLSX/ODS/TSV/PDF paths; XLS output skipped (xlwt unavailable)"
        xls = temp / "out.xls"
        spreadsheet_converter.convert_spreadsheet(source, xls, "xls")
        if not xls.is_file() or xls.stat().st_size <= 0:
            raise AssertionError("XLS output missing")
    return "CSV/XLSX/XLS/ODS/TSV/PDF"


def test_model_conversion():
    trimesh = require_module("trimesh")
    import model_converter

    with tempfile.TemporaryDirectory() as temp:
        temp = pathlib.Path(temp)
        source = temp / "source.obj"
        trimesh.creation.box().export(source)
        for fmt in ["stl", "ply", "glb"]:
            target = temp / f"out.{fmt}"
            model_converter.convert_model(source, target, fmt)
            if not target.is_file() or target.stat().st_size <= 0:
                raise AssertionError(f"{fmt} output missing")
    return "OBJ -> STL/PLY/GLB"


def test_archive_wrapper():
    import archive_manager

    captured = []
    original_run = archive_manager.run_7zip

    def capture(arguments):
        captured.append(list(arguments))
        archive_path = pathlib.Path(arguments[3])
        archive_path.write_bytes(b"fake")
        return 0

    with tempfile.TemporaryDirectory() as alias_temp:
        alias_temp = pathlib.Path(alias_temp)
        source = alias_temp / "one.txt"
        source.write_text("one", encoding="utf-8")
        archive_manager.run_7zip = capture
        try:
            archive_manager.create_archive(alias_temp / "one.gz", [source])
            archive_manager.create_archive(alias_temp / "one.bz2", [source])
        finally:
            archive_manager.run_7zip = original_run

    if "-tgzip" not in captured[0] or "-tbzip2" not in captured[1]:
        raise AssertionError("gz/bz2 format aliases did not map to 7-Zip type names")

    real = archive_manager._find_existing_7zip()
    if real is not None:
        with tempfile.TemporaryDirectory() as temp:
            temp = pathlib.Path(temp)
            source = temp / "hello.txt"
            source.write_text("hello", encoding="utf-8")
            archive = temp / "test.7z"
            archive_manager.create_archive(archive, [source])
            archive_manager.test_archive(archive)
            output = temp / "extracted"
            archive_manager.extract_archive(archive, output)
            if not (output / "hello.txt").is_file():
                raise AssertionError("real 7-Zip extraction missing file")
        return f"real 7-Zip binary: {real}"

    # No real 7-Zip in the sandbox: verify the wrapper's command plumbing
    # with a fake executable and separately test Linux bootstrap below.
    with tempfile.TemporaryDirectory() as temp:
        temp = pathlib.Path(temp)
        fake = temp / "7z"
        fake.write_text(
            "#!/usr/bin/env python3\n"
            "import pathlib, sys\n"
            "a=sys.argv[1:]\n"
            "cmd=a[0]\n"
            "if cmd=='a':\n"
            " out=next(x for x in a[1:] if not x.startswith('-')); "
            "pathlib.Path(out).write_bytes(b'fake')\n"
            "elif cmd=='x':\n"
            " o=next(x[2:] for x in a if x.startswith('-o')); "
            "pathlib.Path(o).mkdir(parents=True,exist_ok=True); "
            "(pathlib.Path(o)/'ok.txt').write_text('ok')\n"
            "sys.exit(0)\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        old = os.environ.get("UWUCONVERTER_7ZIP")
        os.environ["UWUCONVERTER_7ZIP"] = str(fake)
        try:
            source = temp / "hello.txt"
            source.write_text("hello", encoding="utf-8")
            archive = temp / "test.7z"
            archive_manager.create_archive(archive, [source])
            out = temp / "out"
            archive_manager.extract_archive(archive, out)
            if not (out / "ok.txt").is_file():
                raise AssertionError("fake extraction route failed")
        finally:
            if old is None:
                os.environ.pop("UWUCONVERTER_7ZIP", None)
            else:
                os.environ["UWUCONVERTER_7ZIP"] = old
    return "wrapper paths with fake 7-Zip (real binary unavailable)"


def test_linux_7zip_bootstrap():
    import archive_manager

    if not sys.platform.startswith("linux"):
        raise SkipTest("not Linux")

    with tempfile.TemporaryDirectory() as temp:
        temp = pathlib.Path(temp)
        payload = temp / "payload"
        payload.mkdir()
        seven = payload / "7zz"
        seven.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        seven.chmod(0o755)
        package = temp / "7zip.tar.xz"
        with tarfile.open(package, "w:xz") as archive:
            archive.add(seven, arcname="7zz")

        fake_home = temp / "home"
        fake_home.mkdir()
        old_home = os.environ.get("HOME")
        old_urlretrieve = archive_manager.urllib.request.urlretrieve
        old_arch = archive_manager._linux_7zip_architecture

        def fake_download(url, destination):
            shutil.copy2(package, destination)
            return str(destination), None

        archive_manager.urllib.request.urlretrieve = fake_download
        archive_manager._linux_7zip_architecture = lambda: "x86_64"
        os.environ["HOME"] = str(fake_home)
        try:
            # pathlib.Path.home() caches nothing; HOME is read at call time on Unix.
            archive_manager._install_7zip_linux()
            target = fake_home / ".local/share/UwUConverter/tools/7zip/7zz"
            if not target.is_file() or not os.access(target, os.X_OK):
                raise AssertionError("private 7zz was not installed")
        finally:
            archive_manager.urllib.request.urlretrieve = old_urlretrieve
            archive_manager._linux_7zip_architecture = old_arch
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home
    return "private per-user 7zz extraction/install"


def test_audio_video_runtime():
    try:
        import av  # noqa: F401
    except Exception as error:
        raise SkipTest(f"PyAV unavailable in sandbox: {error}")

    if shutil.which("ffmpeg") is None:
        raise SkipTest("ffmpeg command unavailable for generating sample media")

    import audio_converter
    import video_converter
    import media_compression

    with tempfile.TemporaryDirectory() as temp:
        temp = pathlib.Path(temp)
        sample = temp / "sample.mp4"
        result = subprocess.run(
            [
                "ffmpeg", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "testsrc=size=64x64:rate=10",
                "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
                "-t", "1",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                str(sample),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise SkipTest("could not generate sample media: " + result.stderr.strip())

        for fmt in ["mp4", "mkv", "mov", "avi", "webm"]:
            target = temp / f"video.{fmt}"
            video_converter.convert_video(sample, target, fmt)
            if not target.is_file() or target.stat().st_size <= 0:
                raise AssertionError(f"video {fmt} failed")

        for fmt in ["mp3", "wav", "flac", "ogg", "opus"]:
            target = temp / f"audio.{fmt}"
            audio_converter.convert_audio(sample, target, fmt)
            if not target.is_file() or target.stat().st_size <= 0:
                raise AssertionError(f"audio {fmt} failed")

        lossless = pathlib.Path(
            media_compression.compress_video_lossless(sample)
        )
        percent = pathlib.Path(
            media_compression.compress_video_by_percent(sample, 40)
        )
        for output in [lossless, percent]:
            if not output.is_file() or output.stat().st_size <= 0:
                raise AssertionError("video compression failed")
    return "all video/audio outputs + video lossless/percentage compression"


def test_gui_imports():
    require_module("tkinter")
    # Do not create windows in CI/headless environments; verify the GUI modules import.
    import batch_dialog  # noqa: F401
    return "Tkinter + batch dialog module import"


def test_windows_structural():
    make_key = (ROOT / "make_key.py").read_text(encoding="utf-8")
    installer = (ROOT / "installer.iss").read_text(encoding="utf-8")
    for item in [
        "ARCHIVE_EXTENSIONS",
        "AddArchiveMenus",
        "Extract With UwUConverter",
    ]:
        if item not in make_key:
            raise AssertionError(f"make_key.py missing {item}")
    for forbidden in ["SplitString(", "raise Exception.Create"]:
        if forbidden in installer:
            raise AssertionError(f"installer still contains known invalid construct: {forbidden}")
    if "UwUConverterUpdater" not in installer:
        raise AssertionError("Windows updater not installed")
    return "registry/archive/updater wiring scanned; Windows runtime not available here"


def main():
    tests = [
        ("Python syntax", test_python_syntax),
        ("Linux shell syntax", test_shell_syntax),
        ("CLI parser", test_cli_parser),
        ("CLI formats", test_cli_formats_output),
        ("Updater logic", test_updater_logic),
        ("Linux updater package extraction", test_updater_linux_package_extract),
        ("Linux updater install/autostart wiring", test_linux_autostart_install_script),
        ("Linux install/uninstall runtime", test_linux_install_uninstall_runtime),
        ("KDE/Dolphin right-click menus", test_linux_menu_generation),
        ("Batch conversion engine", test_batch_engine),
        ("Image conversion", test_image_conversion),
        ("Image compression", test_image_compression),
        ("Document conversion", test_document_conversion),
        ("Spreadsheet conversion", test_spreadsheet_conversion),
        ("3D model conversion", test_model_conversion),
        ("Archive manager", test_archive_wrapper),
        ("Linux 7-Zip bootstrap", test_linux_7zip_bootstrap),
        ("Audio/video runtime", test_audio_video_runtime),
        ("Batch GUI imports", test_gui_imports),
        ("Windows structural checks", test_windows_structural),
    ]

    for name, func in tests:
        check(name, func)

    passed = sum(1 for _, status, _ in RESULTS if status == "PASS")
    skipped = sum(1 for _, status, _ in RESULTS if status == "SKIP")
    failed = sum(1 for _, status, _ in RESULTS if status == "FAIL")

    print()
    print(f"Summary: {passed} passed, {skipped} skipped, {failed} failed")

    if skipped:
        print(
            "Skipped tests require dependencies/platform capabilities "
            "unavailable in this environment."
        )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
