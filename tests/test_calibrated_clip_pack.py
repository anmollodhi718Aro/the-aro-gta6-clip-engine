"""Tests for calibrated clip-pack mapping and safe review exports."""
import csv
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.clock_sync import ClockAnchor
from backend.app.clip_pack import map_candidates_with_sync, write_clip_pack


class CalibratedClipPackTests(unittest.TestCase):
    def setUp(self):
        self.origin = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
        self.anchors = [
            ClockAnchor("stream-a", self.origin, 8.0),
            ClockAnchor("stream-a", self.origin + timedelta(seconds=60), 68.0),
            ClockAnchor("stream-a", self.origin + timedelta(seconds=120), 128.0),
        ]

    def candidate(self, start=30, end=60, source="stream-a"):
        return {
            "source_id": source, "score": 87, "peak_message_count": 21,
            "peak_window_start": (self.origin + timedelta(seconds=40)).isoformat(),
            "clip_start": (self.origin + timedelta(seconds=start)).isoformat(),
            "clip_end": (self.origin + timedelta(seconds=end)).isoformat(),
        }

    def test_uses_measured_media_offset_not_chat_elapsed_seconds(self):
        row = map_candidates_with_sync([self.candidate()], self.anchors)[0]
        self.assertEqual(row["start_seconds"], 38.0)
        self.assertEqual(row["end_seconds"], 68.0)
        self.assertEqual(row["duration_seconds"], 30.0)
        self.assertTrue(row["renderable"])

    def test_rejects_candidate_from_different_source(self):
        with self.assertRaisesRegex(ValueError, "does not match calibrated source"):
            map_candidates_with_sync([self.candidate(source="other")], self.anchors)

    def test_rejects_candidate_before_calibration_window(self):
        with self.assertRaisesRegex(ValueError, "outside the calibrated interval"):
            map_candidates_with_sync([self.candidate(start=-1, end=20)], self.anchors)

    def test_rejects_candidate_after_calibration_window(self):
        with self.assertRaisesRegex(ValueError, "outside the calibrated interval"):
            map_candidates_with_sync([self.candidate(start=110, end=121)], self.anchors)

    def test_rejects_invalid_candidate_bounds(self):
        with self.assertRaisesRegex(ValueError, "clip_end <= clip_start"):
            map_candidates_with_sync([self.candidate(start=40, end=30)], self.anchors)

    def test_marks_long_candidate_not_renderable(self):
        row = map_candidates_with_sync([self.candidate(start=0, end=181)], self.anchors)[0]
        self.assertFalse(row["renderable"])
        self.assertIn("180-second", row["review_note"])

    def test_rejects_empty_or_bad_calibration(self):
        with self.assertRaisesRegex(ValueError, "at least three"):
            map_candidates_with_sync([self.candidate()], self.anchors[:2])

    def test_writes_csv_and_markdown_review_files(self):
        rows = map_candidates_with_sync([self.candidate()], self.anchors)
        with tempfile.TemporaryDirectory() as folder:
            csv_path, md_path = write_clip_pack(rows, folder)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                saved = list(csv.DictReader(handle))
            self.assertEqual(saved[0]["start_seconds"], "38.0")
            self.assertIn("at least three measured anchors", md_path.read_text(encoding="utf-8"))

    def test_never_overwrites_existing_review_files(self):
        rows = map_candidates_with_sync([self.candidate()], self.anchors)
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "clip_candidates.csv"
            target.write_text("keep this", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                write_clip_pack(rows, folder)
            self.assertEqual(target.read_text(encoding="utf-8"), "keep this")


if __name__ == "__main__":
    unittest.main()
