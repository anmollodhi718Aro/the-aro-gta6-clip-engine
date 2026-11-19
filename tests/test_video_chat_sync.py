import unittest
from datetime import datetime, timezone

from backend.app.models import CandidateMoment
from backend.app.video_chat_sync import (
    ClockOffset,
    candidate_to_video_window,
    map_chat_timestamp_to_video_seconds,
)


class VideoChatSyncTests(unittest.TestCase):
    def setUp(self):
        self.origin = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.offset = ClockOffset(
            offset_seconds=5.0,
            measured_by="operator",
            measured_at=self.origin,
            uncertainty_seconds=0.5,
        )
        self.candidate = CandidateMoment(
            source_id="stream-1",
            peak_window_start=self.origin,
            clip_start=self.origin,
            clip_end=self.origin.replace(minute=0, second=10),
            peak_message_count=20,
            baseline_average=2.0,
            score=80,
            explanation="synthetic test candidate",
        )

    def test_maps_chat_time_using_explicit_offset(self):
        self.assertEqual(
            map_chat_timestamp_to_video_seconds(self.origin, self.origin, self.offset),
            5.0,
        )

    def test_maps_candidate_window_and_requires_review(self):
        result = candidate_to_video_window(
            self.candidate, self.origin, self.offset, video_duration_seconds=30
        )
        self.assertEqual(result.start_seconds, 5.0)
        self.assertEqual(result.end_seconds, 15.0)
        self.assertEqual(result.confidence, "operator_measured")
        self.assertEqual(result.to_dict()["status"], "needs_review")

    def test_rejects_window_beyond_video(self):
        with self.assertRaisesRegex(ValueError, "exceeds video duration"):
            candidate_to_video_window(
                self.candidate, self.origin, self.offset, video_duration_seconds=12
            )

    def test_rejects_negative_mapped_timestamp(self):
        negative = ClockOffset(-20, "operator", self.origin)
        with self.assertRaisesRegex(ValueError, "before the video origin"):
            map_chat_timestamp_to_video_seconds(self.origin, self.origin, negative)

    def test_rejects_naive_timestamps(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            map_chat_timestamp_to_video_seconds(
                datetime(2026, 1, 1), self.origin, self.offset
            )

    def test_marks_uncertain_measurement_low_confidence(self):
        uncertain = ClockOffset(5, "operator", self.origin, uncertainty_seconds=3)
        result = candidate_to_video_window(
            self.candidate, self.origin, uncertain, video_duration_seconds=30
        )
        self.assertEqual(result.confidence, "low")


if __name__ == "__main__":
    unittest.main()
