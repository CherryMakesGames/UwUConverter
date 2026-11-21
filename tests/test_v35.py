"""UwUConverter 3.5 performance regression tests."""
import ast
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]


class StartupTests(unittest.TestCase):
    def test_converter_top_level_does_not_import_heavy_stacks(self):
        tree = ast.parse((ROOT / "Converter.py").read_text(encoding="utf-8"))
        imported = set()

        for node in tree.body:
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])

        self.assertTrue(
            imported.isdisjoint(
                {
                    "av",
                    "PIL",
                    "pandas",
                    "docx",
                    "odf",
                    "reportlab",
                    "trimesh",
                    "rawpy",
                    "tkinter",
                }
            )
        )

    def test_converter_clean_import_does_not_load_conversion_stacks(self):
        code = (
            "import sys; import Converter; "
            "blocked={'av','PIL','pandas','docx','odf','reportlab','trimesh','rawpy','tkinter'}; "
            "loaded={name.split('.')[0] for name in sys.modules}; "
            "assert blocked.isdisjoint(loaded), sorted(blocked & loaded)"
        )
        result = subprocess.run(
            [sys.executable, "-S", "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_browser_host_does_not_load_pillow_before_request(self):
        code = (
            "import sys; import browser_native_host; "
            "assert 'image_converter' not in sys.modules; "
            "assert 'PIL' not in {name.split('.')[0] for name in sys.modules}"
        )
        result = subprocess.run(
            [sys.executable, "-S", "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_document_module_is_light_until_conversion(self):
        code = (
            "import sys; import document_converter; "
            "blocked={'docx','odf','reportlab','pdf2docx'}; "
            "loaded={name.split('.')[0] for name in sys.modules}; "
            "assert blocked.isdisjoint(loaded), sorted(blocked & loaded)"
        )
        result = subprocess.run(
            [sys.executable, "-S", "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


class DuplicatePerformanceTests(unittest.TestCase):
    def test_unique_sizes_do_not_hash_file_contents(self):
        import duplicate_detection

        with tempfile.TemporaryDirectory() as directory:
            first = pathlib.Path(directory) / "first.bin"
            second = pathlib.Path(directory) / "second.bin"
            first.write_bytes(b"a")
            second.write_bytes(b"bb")

            detector = duplicate_detection.DuplicateDetector(enabled=True)

            with mock.patch.object(
                duplicate_detection,
                "file_digest",
                side_effect=AssertionError("unique sizes should not be hashed"),
            ):
                self.assertIsNone(detector.check(first))
                self.assertIsNone(detector.check(second))

    def test_same_size_files_hash_only_when_needed(self):
        import duplicate_detection

        with tempfile.TemporaryDirectory() as directory:
            first = pathlib.Path(directory) / "first.bin"
            second = pathlib.Path(directory) / "second.bin"
            first.write_bytes(b"same")
            second.write_bytes(b"same")

            detector = duplicate_detection.DuplicateDetector(enabled=True)
            calls = []
            real_digest = duplicate_detection.file_digest

            def counted(path):
                calls.append(str(path))
                return real_digest(path)

            with mock.patch.object(
                duplicate_detection,
                "file_digest",
                side_effect=counted,
            ):
                self.assertIsNone(detector.check(first))
                self.assertEqual(detector.check(second), str(first))

            self.assertEqual(len(calls), 2)


class CacheTests(unittest.TestCase):
    def test_settings_default_file_is_cached(self):
        import settings

        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(
                "os.environ",
                {"XDG_CONFIG_HOME": directory},
                clear=False,
            ):
                settings._DEFAULT_CACHE = None
                settings._DEFAULT_CACHE_SIGNATURE = None

                with mock.patch.object(
                    settings,
                    "load_settings",
                    wraps=settings.load_settings,
                ) as loader:
                    settings.get_bool("Operations", "detect_duplicates", True)
                    settings.get_bool("Operations", "detect_duplicates", True)
                    self.assertEqual(loader.call_count, 1)

    def test_7zip_path_is_cached(self):
        import archive_manager

        with tempfile.TemporaryDirectory() as directory:
            executable = pathlib.Path(directory) / "7zz"
            executable.write_bytes(b"fake")
            archive_manager._CACHED_7ZIP = None

            with mock.patch.object(
                archive_manager,
                "_find_existing_7zip",
                return_value=str(executable),
            ) as finder:
                self.assertEqual(archive_manager.find_7zip(), str(executable))
                self.assertEqual(archive_manager.find_7zip(), str(executable))
                self.assertEqual(finder.call_count, 1)


class BatchStartupTests(unittest.TestCase):
    def test_windows_batch_menu_reuses_main_executable(self):
        source = (ROOT / "make_key.py").read_text(encoding="utf-8")
        start = source.index("def command_string")
        end = source.index("def multi_command_string", start)
        command_function = source[start:end]
        self.assertIn('"__BATCH_GUI__"', command_function)
        self.assertNotIn("UwUConverterBatch.exe", command_function)

    def test_linux_batch_menu_reuses_main_executable(self):
        source = (ROOT / "linux_menu.py").read_text(encoding="utf-8")
        start = source.index("def batch_gui_command")
        end = source.index("def make_executable", start)
        command_function = source[start:end]
        self.assertIn('"__BATCH_GUI__"', command_function)
        self.assertNotIn("UwUConverterBatch", command_function)


class FootprintTests(unittest.TestCase):
    def test_spreadsheet_converter_does_not_depend_on_pandas(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertNotIn("pandas", {line.strip().lower() for line in requirements.splitlines()})

        tree = ast.parse((ROOT / "spreadsheet_converter.py").read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertNotIn("pandas", imported)

    def test_browser_host_delegates_conversion_to_main_bundle(self):
        source = (ROOT / "browser_native_host.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])

        self.assertNotIn("image_converter", imported)
        self.assertIn("__BROWSER_CONVERT__", source)
        self.assertIn(
            "__BROWSER_CONVERT__",
            (ROOT / "Converter.py").read_text(encoding="utf-8"),
        )

    def test_release_builds_do_not_ship_legacy_batch_executable(self):
        windows_build = (ROOT / "build_windows.bat").read_text(encoding="utf-8")
        linux_build = (ROOT / "build_linux.sh").read_text(encoding="utf-8")
        windows_ci = (ROOT / ".github/workflows/build-windows.yml").read_text(encoding="utf-8")
        linux_ci = (ROOT / ".github/workflows/build-linux.yml").read_text(encoding="utf-8")

        for source in (windows_build, linux_build, windows_ci, linux_ci):
            self.assertNotIn("--name UwUConverterBatch", source)
            self.assertNotIn("dist\\UwUConverterBatch", source)
            self.assertNotIn("dist/UwUConverterBatch", source)

    def test_spreadsheet_module_import_is_light(self):
        code = (
            "import sys; import spreadsheet_converter; "
            "assert 'pandas' not in {name.split('.')[0] for name in sys.modules}; "
            "assert 'openpyxl' not in {name.split('.')[0] for name in sys.modules}; "
            "assert 'odf' not in {name.split('.')[0] for name in sys.modules}; "
            "assert 'reportlab' not in {name.split('.')[0] for name in sys.modules}"
        )
        result = subprocess.run(
            [sys.executable, "-S", "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


class SpreadsheetRegressionTests(unittest.TestCase):
    def test_csv_roundtrip_without_pandas(self):
        import spreadsheet_converter

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            source = root / "source.csv"
            source.write_text(
                "name,value\na,1\nb,2\n",
                encoding="utf-8",
            )
            xlsx = root / "out.xlsx"
            output = root / "back.csv"

            spreadsheet_converter.convert_spreadsheet(
                source,
                xlsx,
                "xlsx",
            )
            spreadsheet_converter.convert_spreadsheet(
                xlsx,
                output,
                "csv",
            )

            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "name,value\na,1\nb,2\n",
            )


if __name__ == "__main__":
    unittest.main()
