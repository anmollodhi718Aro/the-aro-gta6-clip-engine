"""Tests for read-only multi-video inventory preflight."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.media_batch_preflight import inspect_media_directory, main


GOOD_PROBE = json.dumps({
    "format": {"duration": "42.5", "format_name": "mov,mp4,m4a"},
    "streams": [
        {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080},
        {"codec_type": "audio", "codec_name": "aac"},
    ],
})


class MediaBatchPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "a.mp4").write_bytes(b"synthetic-a")
        (self.root / "b.MOV").write_bytes(b"synthetic-b")
        (self.root / "ignore.txt").write_text("not a video", encoding="utf-8")
        nested = self.root / "nested"
        nested.mkdir()
        (nested / "c.mkv").write_bytes(b"synthetic-c")

    def tearDown(self):
        self.temp.cleanup()

    @patch("backend.app.media_batch_preflight.subprocess.run")
    def test_inspects_all_supported_files_recursively(self, run):
        run.return_value = SimpleNamespace(stdout=GOOD_PROBE)
        report = inspect_media_directory(self.root)
        self.assertEqual(report["files_discovered"], 3)
        self.assertEqual(report["passed"], 3)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(
            [item["path"] for item in report["results"]],
            ["a.mp4", "b.MOV", "nested/c.mkv"],
        )
        self.assertTrue(all(item["duration_seconds"] == 42.5 for item in report["results"]))
        self.assertFalse(report["processing_started"])
        self.assertFalse(report["publishing_enabled"])
        self.assertTrue(report["manual_review_required"])

    @patch("backend.app.media_batch_preflight.subprocess.run")
    def test_keeps_going_after_one_file_fails(self, run):
        run.side_effect = [
            SimpleNamespace(stdout=GOOD_PROBE),
            RuntimeError("corrupt media"),
            SimpleNamespace(stdout=GOOD_PROBE),
        ]
        report = inspect_media_directory(self.root)
        self.assertEqual((report["passed"], report["failed"]), (2, 1))
        self.assertEqual(report["results"][1]["status"], "FAIL")
        self.assertIn("corrupt media", report["results"][1]["error"])

    @patch("backend.app.media_batch_preflight.subprocess.run")
    def test_rejects_audio_only_file(self, run):
        (self.root / "audio.mp4").write_bytes(b"audio")
        run.return_value = SimpleNamespace(stdout=json.dumps({
            "format": {"duration": "10", "format_name": "mp4"},
            "streams": [{"codec_type": "audio", "codec_name": "aac"}],
        }))
        report = inspect_media_directory(self.root, recursive=False)
        item = next(row for row in report["results"] if row["path"] == "audio.mp4")
        self.assertEqual(item["status"], "FAIL")
        self.assertEqual(item["error"], "file has no video stream")

    @patch("backend.app.media_batch_preflight.subprocess.run")
    def test_top_level_only_does_not_include_nested_files(self, run):
        run.return_value = SimpleNamespace(stdout=GOOD_PROBE)
        report = inspect_media_directory(self.root, recursive=False)
        self.assertEqual([item["path"] for item in report["results"]], ["a.mp4", "b.MOV"])

    def test_missing_or_symlink_directory_is_rejected(self):
        with self.assertRaises(FileNotFoundError):
            inspect_media_directory(self.root / "missing")
        with self.assertRaises(ValueError):
            inspect_media_directory(self.root / "ignore.txt")

    @patch("backend.app.media_batch_preflight.subprocess.run")
    def test_symlinked_video_is_reported_as_failure(self, run):
        target = self.root / "a.mp4"
        link = self.root / "linked.mp4"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable on this platform")
        run.return_value = SimpleNamespace(stdout=GOOD_PROBE)
        report = inspect_media_directory(self.root, recursive=False)
        linked = next(item for item in report["results"] if item["path"] == "linked.mp4")
        self.assertEqual(linked["status"], "FAIL")
        self.assertIn("symbolic links", linked["error"])

    @patch("backend.app.media_batch_preflight.subprocess.run")
    def test_invalid_metadata_is_a_per_file_failure(self, run):
        run.return_value = SimpleNamespace(stdout='{"format":{"duration":"NaN"}}')
        report = inspect_media_directory(self.root, recursive=False)
        self.assertEqual(report["failed"], 2)
        self.assertTrue(all(item["error"] for item in report["results"]))


if __name__ == "__main__":
    unittest.main()
