"""Tests for measured chat-to-recording clock calibration."""
import unittest
from datetime import datetime, timedelta, timezone

from backend.app.clock_sync import ClockAnchor, fit_clock_sync


class ClockSyncTests(unittest.TestCase):
    def setUp(self):
        self.origin = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def anchors(self, media_positions=(5.0, 65.0, 125.0)):
        return [
            ClockAnchor("stream-1", self.origin + timedelta(seconds=offset), media)
            for offset, media in zip((0, 60, 120), media_positions)
        ]

    def test_fits_measured_offset_and_maps_inside_interval(self):
        sync = fit_clock_sync(self.anchors())
        self.assertAlmostEqual(sync.map_chat_time(self.origin), 5.0)
        self.assertAlmostEqual(
            sync.map_chat_time(self.origin + timedelta(seconds=30)), 35.0
        )
        self.assertAlmostEqual(sync.map_chat_time(self.origin + timedelta(seconds=120)), 125.0)
        self.assertEqual(sync.source_id, "stream-1")
        self.assertAlmostEqual(sync.drift_ppm, 0.0, places=5)

    def test_accepts_timezone_equivalent_anchor_instants(self):
        anchors = [
            ClockAnchor("stream-1", self.origin, 5),
            ClockAnchor("stream-1", self.origin + timedelta(seconds=60), 65),
            ClockAnchor("stream-1", self.origin + timedelta(seconds=120), 125),
        ]
        sync = fit_clock_sync(anchors)
        alternate_zone = (self.origin + timedelta(seconds=30)).astimezone(
            timezone(timedelta(hours=5, minutes=30))
        )
        self.assertAlmostEqual(sync.map_chat_time(alternate_zone), 35.0)

    def test_requires_three_anchors(self):
        with self.assertRaisesRegex(ValueError, "at least three"):
            fit_clock_sync(self.anchors()[:2])

    def test_normalizes_anchor_source_identity_whitespace(self):
        anchors = [
            ClockAnchor(" stream-1 ", self.origin + timedelta(seconds=offset), media)
            for offset, media in zip((0, 60, 120), (5, 65, 125))
        ]
        sync = fit_clock_sync(anchors)
        self.assertEqual(sync.source_id, "stream-1")

    def test_rejects_inconsistent_source_ids(self):
        anchors = self.anchors()
        anchors[-1] = ClockAnchor("other-stream", anchors[-1].chat_time, 125)
        with self.assertRaisesRegex(ValueError, "same source"):
            fit_clock_sync(anchors)

    def test_rejects_non_increasing_chat_times(self):
        anchors = self.anchors()
        anchors[1] = ClockAnchor("stream-1", self.origin, 65)
        with self.assertRaisesRegex(ValueError, "chat anchor times"):
            fit_clock_sync(anchors)

    def test_rejects_non_increasing_media_positions(self):
        with self.assertRaisesRegex(ValueError, "media anchor positions"):
            fit_clock_sync(self.anchors((5, 4, 125)))

    def test_nonnegative_anchor_positions_produce_nonnegative_fitted_origin(self):
        anchors = self.anchors((0.0, 59.9, 120.0))
        sync = fit_clock_sync(anchors)
        self.assertEqual(sync.media_at_origin, 0.0)
        self.assertEqual(sync.map_chat_time(self.origin), 0.0)
        self.assertGreaterEqual(sync.map_chat_time(self.origin + timedelta(seconds=60)), 0.0)

    def test_constrained_origin_still_obeys_residual_limit(self):
        with self.assertRaisesRegex(ValueError, "residual"):
            fit_clock_sync(
                self.anchors((0.0, 59.9, 120.0)),
                max_residual_seconds=0.05,
            )

    def test_rejects_bad_anchor_residual(self):
        with self.assertRaisesRegex(ValueError, "residual"):
            fit_clock_sync(self.anchors((5, 65, 145)), max_residual_seconds=0.5, max_drift_ppm=1_000_000)

    def test_rejects_excessive_clock_drift(self):
        with self.assertRaisesRegex(ValueError, "drift"):
            fit_clock_sync(self.anchors((5, 65.2, 125.4)), max_drift_ppm=1000)

    def test_rejects_extrapolation_outside_measured_interval(self):
        sync = fit_clock_sync(self.anchors())
        with self.assertRaisesRegex(ValueError, "outside the calibrated interval"):
            sync.map_chat_time(self.origin - timedelta(seconds=1))
        with self.assertRaisesRegex(ValueError, "outside the calibrated interval"):
            sync.map_chat_time(self.origin + timedelta(seconds=121))

    def test_rejects_naive_mapping_timestamp(self):
        sync = fit_clock_sync(self.anchors())
        with self.assertRaisesRegex(ValueError, "timezone"):
            sync.map_chat_time(datetime(2026, 1, 1, 0, 0, 30))

    def test_rejects_invalid_tolerance(self):
        with self.assertRaisesRegex(ValueError, "max_residual_seconds"):
            fit_clock_sync(self.anchors(), max_residual_seconds=float("nan"))
        with self.assertRaisesRegex(ValueError, "max_drift_ppm"):
            fit_clock_sync(self.anchors(), max_drift_ppm=0)


if __name__ == "__main__":
    unittest.main()
