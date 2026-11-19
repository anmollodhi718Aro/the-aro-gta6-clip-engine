import unittest
from datetime import datetime, timezone

from backend.app.models import CandidateMoment
from backend.app.video_chat_sync import VideoWindow
from backend.app.window_selector import SelectionPolicy, select_review_windows


class WindowSelectorTests(unittest.TestCase):
    def make_pair(self, start, end, score, source="stream"):
        origin = datetime(2026, 1, 1, tzinfo=timezone.utc)
        candidate = CandidateMoment(
            source_id=source,
            peak_window_start=origin,
            clip_start=origin,
            clip_end=origin,
            peak_message_count=score,
            baseline_average=1.0,
            score=score,
            explanation="synthetic",
        )
        window = VideoWindow(source, start, end, "operator_measured", 0.0, 0.0)
        return candidate, window

    def test_ranks_candidates_and_returns_chronological_order(self):
        a = self.make_pair(100, 120, 90)
        b = self.make_pair(10, 30, 80)
        result = select_review_windows([a[0], b[0]], [a[1], b[1]])
        self.assertEqual([item["start_seconds"] for item in result], [10, 100])
        self.assertTrue(all(item["human_review_required"] for item in result))
        self.assertTrue(all(item["render_approved"] is False for item in result))

    def test_suppresses_overlapping_windows(self):
        a = self.make_pair(10, 30, 90)
        b = self.make_pair(20, 40, 80)
        result = select_review_windows([a[0], b[0]], [a[1], b[1]])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["candidate_score"], 90)

    def test_applies_count_and_total_duration_limits(self):
        pairs = [self.make_pair(i * 100, i * 100 + 20, 90 - i) for i in range(4)]
        result = select_review_windows(
            [p[0] for p in pairs],
            [p[1] for p in pairs],
            SelectionPolicy(max_clips=2, max_total_duration_seconds=40),
        )
        self.assertEqual(len(result), 2)

    def test_rejects_mismatched_pairing(self):
        a = self.make_pair(0, 20, 90, "one")
        b = self.make_pair(30, 50, 80, "two")
        with self.assertRaisesRegex(ValueError, "source IDs"):
            select_review_windows([a[0]], [b[1]])

    def test_rejects_different_candidate_and_window_counts(self):
        a = self.make_pair(0, 20, 90)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            select_review_windows([a[0]], [])

    def test_rejects_invalid_policy(self):
        with self.assertRaisesRegex(ValueError, "max_clips"):
            SelectionPolicy(max_clips=0)

    def test_long_windows_are_not_selected(self):
        a = self.make_pair(0, 181, 99)
        result = select_review_windows([a[0]], [a[1]])
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
