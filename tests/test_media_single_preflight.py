"""Tests for one-selected-video read-only preflight."""
import json
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
        {"codec_type": "audio", "codec_name": "aac"},
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
    def test_passes_one_selected_file_and_reports_duration(self, run):
        run.return_value = SimpleNamespace(stdout=GOOD_PROBE)
        report = inspect_one_video(self.video)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["duration_seconds"], 42.5)
        self.assertEqual(report["video_streams"][0]["codec"], "h264")
        self.assertFalse(report["processing_started"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        run.assert_called_once()

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
    def test_rejects_malformed_ffprobe_json_shapes(self, run):
        malformed_payloads = (
            [],
            {"format": [], "streams": []},
            {"format": {"duration": "10"}, "streams": None},
            {"format": {"duration": "10"}, "streams": "not-a-list"},
            {"format": {"duration": "10"}, "streams": [None]},
            {"format": {"duration": True}, "streams": []},
            {"format": {"duration": 10 ** 4000}, "streams": []},
        )
        for payload in malformed_payloads:
            with self.subTest(payload_type=type(payload).__name__):
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
