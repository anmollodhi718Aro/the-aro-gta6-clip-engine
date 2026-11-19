"""Tests for measured chat/video clock mapping."""
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from backend.app.media_sync import ClockSync, candidate_media_bounds, render_candidate
from backend.app.models import CandidateMoment

class MediaSyncTests(unittest.TestCase):
    def setUp(self):
        self.media_start = datetime(2026, 11, 19, 10, 0, tzinfo=timezone.utc)
        self.candidate = CandidateMoment(
            source_id="authorized-source",
            peak_window_start=self.media_start + timedelta(seconds=130),
            clip_start=self.media_start + timedelta(seconds=115),
            clip_end=self.media_start + timedelta(seconds=155),
            peak_message_count=12, baseline_average=2.0, score=90,
            explanation="synthetic test candidate")
        self.sync = ClockSync(5.0, 0.25, self.media_start + timedelta(minutes=3),
                              "measured test slate")

    def test_maps_candidate_to_media_seconds(self):
        b = candidate_media_bounds(self.candidate, self.sync, self.media_start, 300)
        self.assertEqual((b.start_seconds, b.end_seconds), (110.0, 150.0))
        self.assertFalse(b.clipped_to_media_bounds)

    def test_clamps_to_media_file_edges(self):
        b = candidate_media_bounds(self.candidate, self.sync, self.media_start, 120)
        self.assertEqual((b.start_seconds, b.end_seconds), (110.0, 120.0))
        self.assertTrue(b.clipped_to_media_bounds)

    def test_rejects_excessive_sync_uncertainty(self):
        uncertain = ClockSync(5, 3, self.media_start, "rough estimate")
        with self.assertRaisesRegex(ValueError, "uncertainty"):
            candidate_media_bounds(self.candidate, uncertain, self.media_start, 300)

    def test_rejects_candidate_outside_media(self):
        with self.assertRaisesRegex(ValueError, "does not overlap"):
            candidate_media_bounds(self.candidate, self.sync, self.media_start, 50)

    def test_rejects_invalid_duration(self):
        with self.assertRaisesRegex(ValueError, "duration"):
            candidate_media_bounds(self.candidate, self.sync, self.media_start, float("nan"))

    def test_rejects_naive_media_start(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            candidate_media_bounds(self.candidate, self.sync, datetime(2026, 11, 19, 10), 300)

    def test_render_calls_existing_local_rights_gated_clipper(self):
        with TemporaryDirectory() as folder:
            source, output = Path(folder) / "authorized.mp4", Path(folder) / "candidate.mp4"
            source.write_bytes(b"placeholder")
            with patch("backend.app.media_sync.render_clip", return_value=output) as render:
                result = render_candidate(self.candidate, self.sync, source, output,
                    media_start_utc=self.media_start, media_duration_seconds=300,
                    rights_confirmed=True)
            self.assertEqual(result, output)
            args, kwargs = render.call_args
            self.assertEqual(args[2:4], (110.0, 150.0))
            self.assertTrue(kwargs["rights_confirmed"])

if __name__ == "__main__":
    unittest.main()
