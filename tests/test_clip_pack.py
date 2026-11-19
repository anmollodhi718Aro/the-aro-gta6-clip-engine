"""Tests for measured media-clock mapping and clip-pack exports."""

import csv
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from backend.app.clip_pack import map_candidates_to_media, write_clip_pack


class ClipPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.origin = datetime(2026, 11, 19, 12, 0, 0, tzinfo=timezone.utc)

    def candidate(self, start: int = 30, end: int = 60) -> dict:
        return {
            "source_id": "authorized-demo",
            "score": 80,
            "peak_message_count": 24,
            "peak_window_start": (self.origin + timedelta(seconds=40)).isoformat(),
            "clip_start": (self.origin + timedelta(seconds=start)).isoformat(),
            "clip_end": (self.origin + timedelta(seconds=end)).isoformat(),
        }

    def test_maps_utc_candidate_to_media_offsets(self) -> None:
        rows = map_candidates_to_media([self.candidate()], self.origin)
        self.assertEqual(rows[0]["start_seconds"], 30.0)
        self.assertEqual(rows[0]["end_seconds"], 60.0)
        self.assertTrue(rows[0]["renderable"])

    def test_normalizes_non_utc_offsets_in_exported_timestamps(self) -> None:
        candidate = self.candidate()
        candidate["clip_start"] = "2026-11-19T17:30:30+05:30"
        candidate["clip_end"] = "2026-11-19T17:31:00+05:30"
        rows = map_candidates_to_media([candidate], self.origin)
        self.assertEqual(rows[0]["clip_start_utc"], "2026-11-19T12:00:30+00:00")
        self.assertEqual(rows[0]["start_seconds"], 30.0)

    def test_rejects_timezone_naive_media_origin(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone"):
            map_candidates_to_media([self.candidate()], "2026-11-19T12:00:00")

    def test_rejects_invalid_candidate_bounds(self) -> None:
        with self.assertRaisesRegex(ValueError, "clip_end"):
            map_candidates_to_media([self.candidate(60, 30)], self.origin)

    def test_marks_candidate_before_recording_as_not_renderable(self) -> None:
        rows = map_candidates_to_media([self.candidate(-10, 20)], self.origin)
        self.assertFalse(rows[0]["renderable"])
        self.assertIn("begins before", rows[0]["review_note"])

    def test_marks_candidate_over_renderer_limit(self) -> None:
        rows = map_candidates_to_media([self.candidate(0, 181)], self.origin)
        self.assertFalse(rows[0]["renderable"])
        self.assertIn("180-second", rows[0]["review_note"])

    def test_exact_renderer_limit_is_allowed_for_review(self) -> None:
        rows = map_candidates_to_media([self.candidate(0, 180)], self.origin)
        self.assertTrue(rows[0]["renderable"])

    def test_writes_csv_and_markdown_review_files(self) -> None:
        rows = map_candidates_to_media([self.candidate()], self.origin)
        with tempfile.TemporaryDirectory() as folder:
            csv_path, markdown_path = write_clip_pack(rows, folder)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                saved = list(csv.DictReader(handle))
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]["start_seconds"], "30.0")
            self.assertIn("Review-ready", markdown_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
