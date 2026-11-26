"""Tests for permission-gated deterministic chat spike detection."""

import unittest
from datetime import datetime, timedelta, timezone

from backend.app.detection import DetectorConfig, detect_chat_spikes
from backend.app.models import ChatEvent, PermissionRecord


class DetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.start = datetime(2026, 11, 18, 12, 0, 0, tzinfo=timezone.utc)
        self.permission = PermissionRecord(
            source_id="sample-stream",
            granted_by="test-creator",
            scopes=frozenset({"analyze_chat"}),
            granted_at=self.start - timedelta(minutes=1),
            expires_at=self.start + timedelta(hours=1),
        )
        self.config = DetectorConfig(
            window_seconds=10,
            baseline_windows=3,
            spike_multiplier=2,
            min_messages=5,
            pre_roll_seconds=15,
            post_roll_seconds=15,
        )

    def make_events(self, counts: list[int]) -> list[ChatEvent]:
        events: list[ChatEvent] = []
        for bucket, count in enumerate(counts):
            for item in range(count):
                events.append(ChatEvent(
                    event_id=f"{bucket}-{item}",
                    source_id="sample-stream",
                    timestamp=self.start + timedelta(seconds=bucket * 10 + item),
                    text="synthetic test event",
                ))
        return events

    def test_rejects_non_finite_or_boolean_spike_multipliers(self) -> None:
        for multiplier in (float("nan"), float("inf"), float("-inf"), True):
            with self.subTest(multiplier=multiplier):
                with self.assertRaisesRegex(ValueError, "finite positive number"):
                    DetectorConfig(spike_multiplier=multiplier)

    def test_rejects_non_integer_detector_count_and_padding_fields(self) -> None:
        invalid_values = (True, 1.5, "2")
        for field_name in (
            "window_seconds",
            "baseline_windows",
            "min_messages",
            "pre_roll_seconds",
            "post_roll_seconds",
        ):
            for value in invalid_values:
                with self.subTest(field=field_name, value=value):
                    with self.assertRaises(ValueError):
                        DetectorConfig(**{field_name: value})

    def test_detects_a_clear_spike(self) -> None:
        candidates = detect_chat_spikes(self.make_events([2, 2, 2, 9]), self.permission, self.config)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].peak_message_count, 9)
        self.assertGreater(candidates[0].score, 50)
        self.assertIn("previous 3-window average", candidates[0].explanation)

    def test_does_not_flag_normal_traffic(self) -> None:
        candidates = detect_chat_spikes(self.make_events([2, 2, 2, 3]), self.permission, self.config)
        self.assertEqual(candidates, [])

    def test_detects_minimum_count_when_above_relative_threshold(self) -> None:
        candidates = detect_chat_spikes(self.make_events([1, 1, 1, 5]), self.permission, self.config)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].peak_message_count, 5)

    def test_duplicate_delivery_does_not_inflate_spike(self) -> None:
        events = self.make_events([2, 2, 2, 5])
        repeated = events + [events[-1], events[-1]]
        candidates = detect_chat_spikes(repeated, self.permission, self.config)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].peak_message_count, 5)

    def test_conflicting_duplicate_id_is_rejected(self) -> None:
        event = ChatEvent("same-id", "sample-stream", self.start, "first")
        conflict = ChatEvent("same-id", "sample-stream", self.start + timedelta(seconds=1), "second")
        with self.assertRaisesRegex(ValueError, "conflicting duplicate"):
            detect_chat_spikes([event, conflict], self.permission, self.config)

    def test_rejects_revoked_permission(self) -> None:
        revoked = PermissionRecord(
            source_id="sample-stream",
            granted_by="test-creator",
            scopes=frozenset({"analyze_chat"}),
            granted_at=self.start - timedelta(minutes=1),
            revoked_at=self.start + timedelta(seconds=15),
        )
        with self.assertRaises(PermissionError):
            detect_chat_spikes(self.make_events([2, 2, 2, 9]), revoked, self.config)

    def test_rejects_wrong_source(self) -> None:
        event = ChatEvent("wrong", "another-stream", self.start)
        with self.assertRaises(ValueError):
            detect_chat_spikes([event], self.permission, self.config)

    def test_rejects_timezone_naive_timestamps(self) -> None:
        with self.assertRaises(ValueError):
            ChatEvent("naive", "sample-stream", datetime(2026, 11, 18, 12, 0, 0))

    def test_rejects_expired_permission(self) -> None:
        expired = PermissionRecord(
            source_id="sample-stream",
            granted_by="test-creator",
            scopes=frozenset({"analyze_chat"}),
            granted_at=self.start - timedelta(minutes=2),
            expires_at=self.start - timedelta(seconds=1),
        )
        with self.assertRaises(PermissionError):
            detect_chat_spikes(self.make_events([2]), expired, self.config)


if __name__ == "__main__":
    unittest.main()
