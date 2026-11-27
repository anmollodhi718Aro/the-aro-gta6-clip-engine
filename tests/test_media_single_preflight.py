"""Tests for one-selected-video read-only preflight."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.media_single_preflight import inspect_one_video, main

GOOD_PROBE = json.dumps({
    "format": {"duration": "42.5", "format_name": "mov,mp4,m4a"},
    "streams": [
        {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080},
        {"codec_type": "audio", "codec_name": "aac", "channels": 2, "sample_rate": "48000"},
    ],
})


class MediaSinglePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.video = self.root / "selected.mp4"
        self.video.write_bytes(b"synthetic-video")

    def tearDown(self):
        self.temp.cleanup()

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_rejects_invalid_video_path_types_before_invoking_process(self, run):
        for video_path in (None, 7, [], {}):
            with self.subTest(video_path=video_path):
                report = inspect_one_video(video_path)
                self.assertEqual(report["status"], "FAIL")
                self.assertIn("video_path must be a non-empty string or pathlib.Path", report["error"])
        for video_path in ("", "   "):
            with self.subTest(video_path=video_path):
                report = inspect_one_video(video_path)
                self.assertEqual(report["status"], "FAIL")
                self.assertIn("video_path must be a non-empty string or pathlib.Path", report["error"])
        run.assert_not_called()

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_invalid_path_object_with_broken_string_conversion_returns_fail(self, run):
        class BrokenPath:
            def __str__(self):
                raise RuntimeError("untrusted string conversion")

        report = inspect_one_video(BrokenPath())
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["selected_file"], "<invalid>")
        self.assertIn("video_path must be a non-empty", report["error"])
        run.assert_not_called()

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_path_subclass_with_broken_string_conversion_is_handled_safely(self, run):
        base_path_type = type(self.video)

        class BrokenPath(base_path_type):
            def __str__(self):
                raise RuntimeError("untrusted Path string conversion")

        run.return_value = SimpleNamespace(stdout=GOOD_PROBE)
        report = inspect_one_video(BrokenPath(self.video))
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["selected_file"], str(self.video))
        run.assert_called_once()
    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_rejects_invalid_ffprobe_executable_before_invoking_process(self, run):
        for executable in ("", "   ", None, 7, Path("ffprobe")):
            with self.subTest(executable=executable):
                report = inspect_one_video(self.video, ffprobe_binary=executable)
                self.assertEqual(report["status"], "FAIL")
                self.assertIn("ffprobe_binary must be a non-empty executable name or path", report["error"])
        run.assert_not_called()

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_passes_one_selected_file_and_reports_duration(self, run):
        run.return_value = SimpleNamespace(stdout=GOOD_PROBE)
        report = inspect_one_video(self.video)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["duration_seconds"], 42.5)
        self.assertEqual(report["video_streams"][0]["codec"], "h264")
        self.assertEqual(report["audio_streams"], [{"codec": "aac", "channels": 2, "sample_rate": "48000"}])
        self.assertFalse(report["processing_started"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        run.assert_called_once()

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_reports_empty_audio_stream_list_without_failing_video_preflight(self, run):
        run.return_value = SimpleNamespace(stdout=json.dumps({
            "format": {"duration": "10", "format_name": "mp4"},
            "streams": [{"codec_type": "video", "codec_name": "h264", "width": 1280, "height": 720}],
        }))
        report = inspect_one_video(self.video)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["audio_streams"], [])
    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_rejects_selected_path_replaced_with_symlink_during_probe(self, run):
        target = self.root / "original-target.mp4"
        selected_original = self.root / "selected-original.mp4"
        target.write_bytes(self.video.read_bytes())
        selected_original.write_bytes(self.video.read_bytes())

        def replace_with_symlink(*_args, **_kwargs):
            self.video.unlink()
            try:
                self.video.symlink_to(target)
            except (OSError, NotImplementedError):
                selected_original.rename(self.video)
                self.skipTest("symlink creation is unavailable on this runner")
            return SimpleNamespace(stdout=GOOD_PROBE)

        run.side_effect = replace_with_symlink
        report = inspect_one_video(self.video)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("became unsafe", report["error"])
        self.assertTrue(self.video.is_symlink())

    @unittest.skipIf(os.name == "nt", "Windows st_ctime is creation time, not change time")
    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_rejects_in_place_mutation_even_when_size_and_mtime_are_restored(self, run):
        before = self.video.stat()

        def mutate_during_probe(*_args, **_kwargs):
            self.video.write_bytes(b"X" * before.st_size)
            os.utime(self.video, ns=(before.st_atime_ns, before.st_mtime_ns))
            return SimpleNamespace(stdout=GOOD_PROBE)

        run.side_effect = mutate_during_probe
        report = inspect_one_video(self.video)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("changed while it was being inspected", report["error"])

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_rejects_selected_path_replaced_with_different_regular_file_during_probe(self, run):
        replacement = self.root / "replacement.mp4"
        replacement_bytes = b"different regular file bytes"
        replacement.write_bytes(replacement_bytes)

        def replace_selected_path(*_args, **_kwargs):
            self.video.unlink()
            replacement.rename(self.video)
            return SimpleNamespace(stdout=GOOD_PROBE)

        run.side_effect = replace_selected_path
        report = inspect_one_video(self.video)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("changed while it was being inspected", report["error"])
        self.assertEqual(self.video.read_bytes(), replacement_bytes)

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_rejects_missing_or_invalid_format_name(self, run):
        for format_name in (None, "", 17):
            with self.subTest(format_name=format_name):
                run.return_value = SimpleNamespace(stdout=json.dumps({
                    "format": {"duration": "10", "format_name": format_name},
                    "streams": [{"codec_type": "video", "codec_name": "h264", "width": 1280, "height": 720}],
                }))
                report = inspect_one_video(self.video)
                self.assertEqual(report["status"], "FAIL")
                self.assertIn("format name", report["error"])

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_rejects_missing_codec_and_invalid_video_dimensions(self, run):
        video_base = {"codec_type": "video", "codec_name": "h264", "width": 1280, "height": 720}
        cases = (
            ({**video_base, "codec_name": None}, "codec name"),
            ({**video_base, "codec_name": ""}, "codec name"),
            ({**video_base, "width": None}, "width"),
            ({**video_base, "width": True}, "width"),
            ({**video_base, "width": 0}, "width"),
            ({**video_base, "height": "720"}, "height"),
            ({**video_base, "height": -1}, "height"),
        )
        for stream, expected_error in cases:
            with self.subTest(stream=stream):
                run.return_value = SimpleNamespace(stdout=json.dumps({
                    "format": {"duration": "10", "format_name": "mp4"},
                    "streams": [stream],
                }))
                report = inspect_one_video(self.video)
                self.assertEqual(report["status"], "FAIL")
                self.assertIn(expected_error, report["error"])

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_rejects_audio_only_file(self, run):
        run.return_value = SimpleNamespace(stdout=json.dumps({
            "format": {"duration": "10", "format_name": "mp4"},
            "streams": [{"codec_type": "audio", "codec_name": "aac"}],
        }))
        report = inspect_one_video(self.video)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["error"], "selected file has no video stream")

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_rejects_non_finite_or_zero_duration(self, run):
        for duration in ("NaN", "0", "-1", "Infinity"):
            run.return_value = SimpleNamespace(stdout=json.dumps({
                "format": {"duration": duration, "format_name": "mp4"},
                "streams": [{"codec_type": "video", "codec_name": "h264"}],
            }))
            self.assertEqual(inspect_one_video(self.video)["status"], "FAIL")

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_rejects_boolean_duration_instead_of_coercing_it_to_seconds(self, run):
        for duration in (True, False):
            with self.subTest(duration=duration):
                run.return_value = SimpleNamespace(stdout=json.dumps({
                    "format": {"duration": duration, "format_name": "mp4"},
                    "streams": [{"codec_type": "video", "codec_name": "h264"}],
                }))
                report = inspect_one_video(self.video)
                self.assertEqual(report["status"], "FAIL")
                self.assertIn("invalid metadata", report["error"])

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_rejects_duration_integer_too_large_for_float_conversion(self, run):
        payload = {
            "format": {"duration": 10 ** 400, "format_name": "mp4"},
            "streams": [{"codec_type": "video", "codec_name": "h264"}],
        }
        run.return_value = SimpleNamespace(stdout=json.dumps(payload))
        report = inspect_one_video(self.video)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("invalid metadata", report["error"])

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_rejects_malformed_ffprobe_metadata_shapes(self, run):
        malformed_payloads = (
            [],
            {"format": None, "streams": []},
            {"format": {"duration": "10"}, "streams": None},
            {"format": {"duration": "10"}, "streams": {}},
            {"format": {"duration": "10"}, "streams": [None]},
        )
        for payload in malformed_payloads:
            with self.subTest(payload=payload):
                run.return_value = SimpleNamespace(stdout=json.dumps(payload))
                report = inspect_one_video(self.video)
                self.assertEqual(report["status"], "FAIL")
                self.assertIn("invalid metadata", report["error"])

    def test_rejects_missing_empty_and_unsupported_files(self):
        self.assertEqual(inspect_one_video(self.root / "missing.mp4")["status"], "FAIL")
        empty = self.root / "empty.mp4"
        empty.touch()
        self.assertIn("empty", inspect_one_video(empty)["error"])
        unsupported = self.root / "notes.txt"
        unsupported.write_text("not video", encoding="utf-8")
        self.assertIn("supported video extension", inspect_one_video(unsupported)["error"])

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_probe_failure_is_a_single_file_failure(self, run):
        run.side_effect = RuntimeError("probe failed")
        report = inspect_one_video(self.video)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("probe failed", report["error"])

    @patch("backend.app.media_single_preflight.subprocess.run")
    def test_cli_writes_exclusive_report_without_upload(self, run):
        run.return_value = SimpleNamespace(stdout=GOOD_PROBE)
        output = self.root / "report.json"
        with patch("sys.argv", ["media_single_preflight", str(self.video), "--output", str(output)]):
            self.assertEqual(main(), 0)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["upload_performed"])
        with patch("sys.argv", ["media_single_preflight", str(self.video), "--output", str(output)]):
            self.assertEqual(main(), 2)


if __name__ == "__main__":
    unittest.main()
