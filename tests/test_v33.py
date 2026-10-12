"""UwUConverter 3.3 regression tests."""
import importlib.util
import pathlib
import tempfile
import unittest

from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parent.parent


class CombinedPdfTests(unittest.TestCase):
    def test_multiple_images_create_one_pdf(self):
        spec = importlib.util.spec_from_file_location(
            "image_converter_v33_test",
            ROOT / "image_converter.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as folder:
            folder = pathlib.Path(folder)
            first = folder / "first.png"
            second = folder / "second.jpg"
            output = folder / "combined.pdf"

            Image.new("RGB", (24, 20), "white").save(first)
            Image.new("RGB", (18, 30), "black").save(second)

            module.convert_images_to_pdf(
                [first, second],
                output,
            )

            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 100)

    def test_combined_pdf_requires_two_images(self):
        spec = importlib.util.spec_from_file_location(
            "image_converter_v33_single_test",
            ROOT / "image_converter.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as folder:
            folder = pathlib.Path(folder)
            first = folder / "first.png"
            output = folder / "combined.pdf"
            Image.new("RGB", (8, 8), "white").save(first)

            with self.assertRaises(ValueError):
                module.convert_images_to_pdf(
                    [first],
                    output,
                )


class KdeMenuTests(unittest.TestCase):
    def _load_linux_menu(self):
        spec = importlib.util.spec_from_file_location(
            "linux_menu_v33_test",
            ROOT / "linux_menu.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_png_menu_only_contains_png_actions(self):
        module = self._load_linux_menu()
        namespace = {}
        exec((ROOT / "file_types.py").read_text(), namespace)
        file_types = namespace["file_types"]

        with tempfile.TemporaryDirectory() as folder:
            module.DOLPHIN_FOLDER = pathlib.Path(folder)
            module.create_dolphin_file_menus(file_types)

            png_menu = pathlib.Path(folder) / "uwuconverter-mime-image-png.desktop"
            text = png_menu.read_text()

            self.assertIn("Convert To JPG", text)
            self.assertIn("Convert To WEBP", text)
            self.assertNotIn("Convert To PNG", text)
            self.assertNotIn("Video Conversions", text)
            self.assertNotIn("Convert To MP4", text)

    def test_jpeg_shared_mime_has_no_duplicate_actions(self):
        module = self._load_linux_menu()
        namespace = {}
        exec((ROOT / "file_types.py").read_text(), namespace)
        file_types = namespace["file_types"]

        with tempfile.TemporaryDirectory() as folder:
            module.DOLPHIN_FOLDER = pathlib.Path(folder)
            module.create_dolphin_file_menus(file_types)

            jpeg_menu = pathlib.Path(folder) / "uwuconverter-mime-image-jpeg.desktop"
            text = jpeg_menu.read_text()

            self.assertEqual(text.count("Convert To PNG"), 1)
            self.assertNotIn("Convert To JPG", text)
            self.assertNotIn("Convert To JPEG", text)

    def test_images_to_pdf_requires_multiple_urls_in_kde(self):
        module = self._load_linux_menu()

        with tempfile.TemporaryDirectory() as folder:
            module.DOLPHIN_FOLDER = pathlib.Path(folder)
            module.create_dolphin_images_to_pdf_menu()

            path = pathlib.Path(folder) / "uwuconverter-images-to-pdf.desktop"
            text = path.read_text()

            self.assertIn("X-KDE-MinNumberOfUrls=2", text)
            self.assertIn("IMAGES_TO_SINGLE_PDF", text)
            self.assertIn("%F", text)

    def test_cleanup_removes_old_and_current_duplicate_menus(self):
        module = self._load_linux_menu()

        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            current = root / "kio/servicemenus"
            legacy = root / "kservices5/ServiceMenus"
            current.mkdir(parents=True)
            legacy.mkdir(parents=True)

            (current / "uwuconverter-new.desktop").write_text("new")
            (legacy / "UwUConverter-old.desktop").write_text("old")
            (legacy / "not-ours.desktop").write_text("keep")

            module.DOLPHIN_SERVICE_FOLDERS = [current, legacy]
            removed = module.cleanup_linux_integrations()

            self.assertFalse((current / "uwuconverter-new.desktop").exists())
            self.assertFalse((legacy / "UwUConverter-old.desktop").exists())
            self.assertTrue((legacy / "not-ours.desktop").exists())
            self.assertEqual(len([x for x in removed if x.endswith('.desktop')]), 2)


class ModernShellTests(unittest.TestCase):
    def test_modern_shell_requires_two_supported_images(self):
        cpp = (ROOT / "windows_modern_shell/UwUConverterShell.cpp").read_text()
        generated = (ROOT / "windows_modern_shell/generate_actions.py").read_text()

        self.assertIn("IMAGES_TO_SINGLE_PDF", generated)
        self.assertIn("IsImagesToPdfAction", cpp)
        self.assertIn("selection.size() < 2", cpp)


if __name__ == "__main__":
    unittest.main()
