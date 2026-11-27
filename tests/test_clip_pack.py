"""Tests for measured media-clock mapping and clip-pack exports."""

import csv
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone

from backend.app.clip_pack import load_clock_sync, map_candidates_to_media, write_clip_pack
from backend.app.clock_sync import ClockAnchor, fit_clock_sync


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


    def test_maps_using_measured_multi_anchor_clock_fit(self) -> None:
        anchors = [
            ClockAnchor("authorized-demo", self.origin + timedelta(seconds=offset), offset + 5)
            for offset in (0, 60, 120)
        ]
        sync = fit_clock_sync(anchors)
        rows = map_candidates_to_media([self.candidate()], clock_sync=sync, source_id="authorized-demo")
        self.assertEqual(rows[0]["start_seconds"], 35.0)
        self.assertEqual(rows[0]["end_seconds"], 65.0)
        self.assertEqual(rows[0]["sync_method"], "measured_multi_anchor_fit")
        self.assertEqual(rows[0]["sync_max_residual_seconds"], 0.0)

    def test_clock_fit_rejects_non_string_candidate_source_id(self) -> None:
        anchors = [
            ClockAnchor("123", self.origin + timedelta(seconds=offset), offset)
            for offset in (0, 60, 120)
        ]
        sync = fit_clock_sync(anchors)
        candidate = self.candidate()
        candidate["source_id"] = 123
        with self.assertRaisesRegex(ValueError, "candidate 1 source_id must be a string"):
            map_candidates_to_media([candidate], clock_sync=sync)

    def test_rejects_non_string_plan_source_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_id must be a non-empty string"):
            map_candidates_to_media([self.candidate()], self.origin, source_id=123)

    def test_single_origin_mapping_rejects_non_string_candidate_source_id(self) -> None:
        candidate = self.candidate()
        candidate["source_id"] = 123
        with self.assertRaisesRegex(ValueError, "candidate 1 source_id must be a string"):
            map_candidates_to_media([candidate], self.origin)

    def test_clock_fit_rejects_source_mismatch(self) -> None:
        anchors = [
            ClockAnchor("different-source", self.origin + timedelta(seconds=offset), offset)
            for offset in (0, 60, 120)
        ]
        sync = fit_clock_sync(anchors)
        with self.assertRaisesRegex(ValueError, "does not match"):
            map_candidates_to_media([self.candidate()], clock_sync=sync, source_id="authorized-demo")

    def test_clock_fit_rejects_candidate_with_missing_source_id(self) -> None:
        anchors = [
            ClockAnchor("authorized-demo", self.origin + timedelta(seconds=offset), offset)
            for offset in (0, 60, 120)
        ]
        sync = fit_clock_sync(anchors)
        candidate = self.candidate()
        candidate.pop("source_id")
        with self.assertRaisesRegex(ValueError, "missing source_id"):
            map_candidates_to_media([candidate], clock_sync=sync)

    def test_clock_fit_rejects_blank_candidate_source_id_without_plan_source(self) -> None:
        anchors = [
            ClockAnchor("authorized-demo", self.origin + timedelta(seconds=offset), offset)
            for offset in (0, 60, 120)
        ]
        sync = fit_clock_sync(anchors)
        candidate = self.candidate()
        candidate["source_id"] = " "
        with self.assertRaisesRegex(ValueError, "missing source_id"):
            map_candidates_to_media([candidate], clock_sync=sync)

    def test_clock_fit_refuses_candidate_outside_calibrated_interval(self) -> None:
        anchors = [
            ClockAnchor("authorized-demo", self.origin + timedelta(seconds=offset), offset)
            for offset in (0, 60, 120)
        ]
        sync = fit_clock_sync(anchors)
        with self.assertRaisesRegex(ValueError, "outside the calibrated interval"):
            map_candidates_to_media([self.candidate(130, 150)], clock_sync=sync, source_id="authorized-demo")

    def test_rejects_boolean_media_seconds_in_clock_anchor_json(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "anchors.json"
            path.write_text(json.dumps({"anchors": [
                {"source_id": "authorized-demo", "chat_time": (self.origin + timedelta(seconds=offset)).isoformat(), "media_seconds": (True if offset == 0 else offset)}
                for offset in (0, 60, 120)
            ]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "finite number"):
                load_clock_sync(path)

    def test_loads_operator_measured_clock_anchor_json(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "anchors.json"
            path.write_text(json.dumps({"anchors": [
                {"source_id": "authorized-demo", "chat_time": (self.origin + timedelta(seconds=offset)).isoformat(), "media_seconds": offset + 5}
                for offset in (0, 60, 120)
            ]}), encoding="utf-8")
            sync = load_clock_sync(path)
            self.assertEqual(sync.source_id, "authorized-demo")
            self.assertAlmostEqual(sync.rate, 1.0)

    def test_writes_csv_and_markdown_review_files(self) -> None:
        rows = map_candidates_to_media([self.candidate()], self.origin)
        with tempfile.TemporaryDirectory() as folder:
            csv_path, markdown_path = write_clip_pack(rows, folder)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                saved = list(csv.DictReader(handle))
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]["start_seconds"], "30.0")
            self.assertIn("Review-ready", markdown_path.read_text(encoding="utf-8"))

    def test_existing_clip_pack_outputs_are_never_overwritten(self) -> None:
        rows = map_candidates_to_media([self.candidate()], self.origin)
        with tempfile.TemporaryDirectory() as folder:
            csv_path = Path(folder) / "clip_candidates.csv"
            markdown_path = Path(folder) / "clip_candidates.md"
            csv_path.write_text("owner-reviewed-csv", encoding="utf-8")
            markdown_path.write_text("owner-reviewed-markdown", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                write_clip_pack(rows, folder)
            self.assertEqual(csv_path.read_text(encoding="utf-8"), "owner-reviewed-csv")
            self.assertEqual(markdown_path.read_text(encoding="utf-8"), "owner-reviewed-markdown")


    def test_partial_publish_collision_preserves_outputs_without_racy_unlink(self) -> None:
        rows = map_candidates_to_media([self.candidate()], self.origin)
        with tempfile.TemporaryDirectory() as folder:
            markdown_path = Path(folder) / "clip_candidates.md"
            markdown_path.write_text("another run owns this file", encoding="utf-8")
            csv_path = Path(folder) / "clip_candidates.csv"
            real_unlink = Path.unlink
            unlink_targets = []

            def record_unlink(path, *args, **kwargs):
                if path == csv_path:
                    unlink_targets.append(path)
                return real_unlink(path, *args, **kwargs)

            from unittest.mock import patch
            with patch.object(Path, "unlink", new=record_unlink):
                with self.assertRaisesRegex(OSError, "already-published output"):
                    write_clip_pack(rows, folder)

            # The first output remains available for owner inspection. The
            # collision target is untouched, and rollback never unlinks by
            # pathname after a separate identity check.
            self.assertTrue(csv_path.exists())
            self.assertIn("authorized-demo", csv_path.read_text(encoding="utf-8"))
            self.assertEqual(unlink_targets, [])
            self.assertEqual(markdown_path.read_text(encoding="utf-8"), "another run owns this file")


if __name__ == "__main__":
    unittest.main()
