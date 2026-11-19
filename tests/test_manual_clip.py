"""Tests for manual local clip-session preparation."""
import csv
import tempfile
import unittest
from pathlib import Path

from backend.app.manual_clip import build_manual_rows, write_manual_csv


class ManualClipTests(unittest.TestCase):
    def test_builds_batch_render_compatible_rows(self):
        rows = build_manual_rows({
            "source_id": "owned-local-recording",
            "clips": [
                {"start_seconds": 12.5, "end_seconds": 42.5, "note": "reviewed moment"},
            ],
        })
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["start_seconds"], 12.5)
        self.assertEqual(rows[0]["end_seconds"], 42.5)
        self.assertEqual(rows[0]["renderable"], "true")
        self.assertEqual(rows[0]["sync_method"], "manual_local_media_time")

    def test_rejects_invalid_or_overlong_ranges(self):
        invalid = [
            {"start_seconds": -1, "end_seconds": 10},
            {"start_seconds": 10, "end_seconds": 10},
            {"start_seconds": 0, "end_seconds": 181},
            {"start_seconds": float("nan"), "end_seconds": 10},
            {"start_seconds": True, "end_seconds": 10},
        ]
        for clip in invalid:
            with self.subTest(clip=clip), self.assertRaises(ValueError):
                build_manual_rows({"source_id": "recording", "clips": [clip]})

    def test_rejects_missing_source_and_empty_clips(self):
        with self.assertRaises(ValueError):
            build_manual_rows({"source_id": "", "clips": [{"start_seconds": 0, "end_seconds": 5}]})
        with self.assertRaises(ValueError):
            build_manual_rows({"source_id": "recording", "clips": []})

    def test_writes_csv_and_refuses_to_overwrite(self):
        rows = build_manual_rows({
            "source_id": "recording",
            "clips": [{"start_seconds": 1, "end_seconds": 8}],
        })
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "manual.csv"
            write_manual_csv(rows, target)
            with target.open(encoding="utf-8", newline="") as handle:
                saved = list(csv.DictReader(handle))
            self.assertEqual(saved[0]["source_id"], "recording")
            self.assertEqual(saved[0]["start_seconds"], "1.0")
            with self.assertRaises(FileExistsError):
                write_manual_csv(rows, target)
            self.assertEqual(len(list(Path(folder).iterdir())), 1)


if __name__ == "__main__":
    unittest.main()
