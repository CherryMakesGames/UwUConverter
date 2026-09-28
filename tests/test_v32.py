"""3.2 regression tests. Run: python -m unittest discover -s tests -v"""
import importlib.util
import pathlib
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import settings
import duplicate_detection


class SettingsTests(unittest.TestCase):
    def test_settings_defaults_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as root:
            path = pathlib.Path(root) / "settings.ini"
            config = settings.load_settings(path)
            self.assertTrue(settings.enabled("archive", config))
            self.assertTrue(settings.get_bool("Operations", "auto_close_success", True, config))
            config.add_section("ContextMenu")
            config.set("ContextMenu", "archive", "false")
            config.add_section("Operations")
            config.set("Operations", "auto_close_success", "false")
            settings.save_settings(config, path)
            loaded = settings.load_settings(path)
            self.assertFalse(settings.enabled("archive", loaded))
            self.assertFalse(settings.get_bool("Operations", "auto_close_success", True, loaded))

    def test_category_filter_is_recursive(self):
        from file_types import file_types
        cfg = settings.load_settings()
        if not cfg.has_section("ContextMenu"):
            cfg.add_section("ContextMenu")
        cfg.set("ContextMenu", "compression", "false")
        filtered = settings.filter_file_types(file_types, cfg)
        def flatten(items):
            for _, _, action in items:
                if isinstance(action, list):
                    yield from flatten(action)
                else:
                    yield action.lower()
        self.assertFalse(any("compress" in action for action in flatten(filtered[".png"])))
        self.assertTrue(any("webp" in action for action in flatten(filtered[".png"])))

    def test_menu_categories(self):
        self.assertEqual(settings.category_for_action("ARCHIVE_EXTRACT_HERE"), "archive")
        self.assertEqual(settings.category_for_action("VIDEO_COMPRESS_50"), "compression")
        self.assertEqual(settings.category_for_action("WEBP", ".png"), "image")
        self.assertEqual(settings.category_for_action("MP3", ".mp4"), "audio")


class DuplicateTests(unittest.TestCase):
    def test_identical_bytes_detected_without_deletion(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            a, b, c = (root / f for f in ("a.txt", "b.txt", "c.txt"))
            a.write_bytes(b"identical")
            b.write_bytes(b"identical")
            c.write_bytes(b"different")
            detector = duplicate_detection.DuplicateDetector(enabled=True)
            self.assertIsNone(detector.check(a))
            self.assertEqual(detector.check(b), str(a))
            self.assertIsNone(detector.check(c))
            self.assertEqual(a.read_bytes(), b"identical")
            self.assertEqual(b.read_bytes(), b"identical")
            self.assertEqual(duplicate_detection.duplicate_groups([a, b, c]), {str(a): [str(b)]})

    def test_disabled_duplicate_detection(self):
        with tempfile.TemporaryDirectory() as folder:
            source = pathlib.Path(folder) / "file"
            source.write_bytes(b"x")
            detector = duplicate_detection.DuplicateDetector(enabled=False)
            self.assertIsNone(detector.check(source))
            self.assertIsNone(detector.check(source))

    def test_planned_output_filename_collision(self):
        import batch_converter
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            a = root / "photo.png"
            b = root / "photo.jpg"
            c = root / "other.png"
            for file in (a, b, c):
                file.write_bytes(file.name.encode())
            collisions = batch_converter.find_output_collisions([a, b, c], "webp")
            self.assertEqual(len(collisions), 1)
            self.assertEqual(collisions["photo.webp"], [str(a), str(b)])

    def test_actual_batch_duplicate_skip(self):
        import batch_converter
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            (root / "a.png").write_bytes(b"identical")
            (root / "b.png").write_bytes(b"identical")
            processed = []
            original = batch_converter.convert_one
            def fake_convert(path, *args, **kwargs):
                processed.append(path.name)
                return "converted"
            batch_converter.convert_one = fake_convert
            try:
                with mock.patch.object(batch_converter, 'DuplicateDetector', return_value=duplicate_detection.DuplicateDetector(enabled=True)):
                    stats = batch_converter.batch_convert_folder(root, 'batch_image_beside_webp')
            finally:
                batch_converter.convert_one = original
            self.assertEqual(stats['matched'], 2)
            self.assertEqual(stats['skipped'], 1)
            self.assertEqual(stats['converted'], 1)
            self.assertEqual(len(processed), 1)


class CodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Test the real decision-making against a lightweight fake AV module.
        cls.previous = sys.modules.get('av')
        sys.modules['av'] = types.ModuleType('av')
        spec = importlib.util.spec_from_file_location('video32_test', ROOT / 'video_converter.py')
        cls.video = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.video)

    @classmethod
    def tearDownClass(cls):
        if cls.previous is None:
            sys.modules.pop('av', None)
        else:
            sys.modules['av'] = cls.previous

    def stream(self, kind, codec):
        return types.SimpleNamespace(type=kind, codec_context=types.SimpleNamespace(name=codec))

    def test_mp4_unsupported_video_codec_transcodes(self):
        inp = types.SimpleNamespace(streams=[self.stream('video', 'vp9'), self.stream('audio', 'opus')])
        self.assertTrue(self.video.needs_transcoding(inp, 'mp4'))

    def test_mp4_compatible_codec_remuxes(self):
        inp = types.SimpleNamespace(streams=[self.stream('video', 'h264'), self.stream('audio', 'aac')])
        self.assertFalse(self.video.needs_transcoding(inp, 'mp4'))

    def test_webm_incompatible_codec_transcodes(self):
        inp = types.SimpleNamespace(streams=[self.stream('video', 'h264'), self.stream('audio', 'aac')])
        self.assertTrue(self.video.needs_transcoding(inp, 'webm'))

    def test_mkv_unknown_codecs_try_remux(self):
        inp = types.SimpleNamespace(streams=[self.stream('video', 'vp9')])
        self.assertFalse(self.video.needs_transcoding(inp, 'mkv'))

    def test_installed_encoder_fallback(self):
        with mock.patch.object(self.video, '_encoder_available', side_effect=lambda x: x == 'mpeg4'):
            self.assertEqual(self.video.choose_encoder(['libx264', 'h264', 'mpeg4']), 'mpeg4')
        with mock.patch.object(self.video, '_encoder_available', return_value=False):
            with self.assertRaises(RuntimeError):
                self.video.choose_encoder(['libx264'])


class IntegrationTests(unittest.TestCase):
    def test_version_consistency(self):
        namespace = {}
        exec((ROOT / 'version.py').read_text(), namespace)
        self.assertEqual(namespace['APP_VERSION'], '3.2.0')
        self.assertIn('#define MyAppVersion "3.2.0"', (ROOT / 'installer.iss').read_text())
        self.assertIn('Version="3.2.0.0"', (ROOT / 'windows_modern_shell/generated/package/AppxManifest.xml').read_text())

    def test_autoclose_success_only(self):
        text = (ROOT / 'archive_progress_ui.py').read_text()
        self.assertIn('if self.success and self.auto_close_success.get()', text)
        self.assertIn('self.window.after(650, self.window.destroy)', text)
        self.assertIn('"auto_close_success", True', text)
        batch = (ROOT / 'batch_dialog.py').read_text()
        self.assertIn('payload["failed"] == 0 and get_bool(', batch)

    def test_native_shell_honors_ini(self):
        cpp = (ROOT / 'windows_modern_shell/UwUConverterShell.cpp').read_text()
        self.assertIn('GetPrivateProfileIntW', cpp)
        self.assertIn('UserAllowsAction(kUwUActions[index])', cpp)

    def test_browser_archives(self):
        import zipfile
        for browser in ('Chromium', 'Firefox'):
            path = ROOT / f'browser_extension/dist/UwUConverter-{browser}.zip'
            with zipfile.ZipFile(path) as package:
                self.assertIsNone(package.testzip())
                self.assertTrue(any(name.endswith('manifest.json') for name in package.namelist()))


if __name__ == '__main__':
    unittest.main()
