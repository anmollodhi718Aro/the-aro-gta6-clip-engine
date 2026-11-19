import unittest
from datetime import datetime, timedelta, timezone

from backend.app.creator_watchlist import (
    DEFAULT_CREATORS,
    SevenDayMetrics,
    rank_seven_day_creators,
    ranking_report,
)

START = datetime(2026, 11, 12, tzinfo=timezone.utc)
END = START + timedelta(days=7)
SOURCE = "https://www.youtube.com/watch?v=example"


def metric(creator_id, views, peak=0, average=0.0, **overrides):
    values = dict(
        creator_id=creator_id,
        window_start=START,
        window_end=END,
        views=views,
        live_streams=1,
        peak_concurrent_viewers=peak,
        average_concurrent_viewers=average,
        source_url=SOURCE,
    )
    values.update(overrides)
    return SevenDayMetrics(**values)


class CreatorWatchlistTests(unittest.TestCase):
    def test_candidate_list_contains_user_requested_names_and_exact_id(self):
        creators = {creator.creator_id: creator.display_name for creator in DEFAULT_CREATORS}
        self.assertEqual(creators["death-tracks-gaming"], "Death Tracks Gaming")
        self.assertIn("Death Rush Gaming", creators.values())
        self.assertIn("iShowSpeed", creators.values())
        self.assertIn("Techno Gamerz", creators.values())
        self.assertIn("CarryisLive", creators.values())
        self.assertEqual(len(DEFAULT_CREATORS), 16)

    def test_ranks_by_seven_day_views(self):
        rows = rank_seven_day_creators([
            metric("mythpat", 900),
            metric("tgg", 1200),
            metric("techno-gamerz", 1200, peak=40),
        ])
        self.assertEqual([row["creator_id"] for row in rows],
                         ["techno-gamerz", "tgg", "mythpat"])

    def test_live_audience_breaks_view_ties(self):
        rows = rank_seven_day_creators([
            metric("mythpat", 1000, peak=20),
            metric("tgg", 1000, peak=50),
        ])
        self.assertEqual(rows[0]["creator_id"], "tgg")

    def test_missing_metrics_are_not_fabricated(self):
        self.assertEqual(len(rank_seven_day_creators([metric("mythpat", 10)])), 1)

    def test_rejects_naive_timestamps(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            metric("mythpat", 10, window_start=datetime(2026, 11, 12),
                   window_end=datetime(2026, 11, 19)).validate()

    def test_rejects_wrong_window(self):
        with self.assertRaisesRegex(ValueError, "exactly seven days"):
            metric("mythpat", 10, window_end=END - timedelta(hours=1)).validate()

    def test_rejects_negative_metrics(self):
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            metric("mythpat", -1).validate()

    def test_rejects_boolean_and_fractional_count_metrics(self):
        for field, value in (
            ("views", True),
            ("views", 1.5),
            ("live_streams", False),
            ("peak_concurrent_viewers", 2.5),
        ):
            with self.subTest(field=field, value=value):
                with self.assertRaisesRegex(ValueError, "non-negative integer"):
                    metric("mythpat", 10, **{field: value}).validate()

    def test_rejects_non_finite_or_boolean_average_viewers(self):
        for value in (True, float("nan"), float("inf"), -float("inf"), -0.1):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "finite non-negative"):
                    metric("mythpat", 10, average=value).validate()

    def test_requires_https_evidence_url(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            metric("mythpat", 10, source_url="http://example.com").validate()

    def test_rejects_duplicate_rows(self):
        with self.assertRaisesRegex(ValueError, "duplicate metrics"):
            rank_seven_day_creators([metric("mythpat", 10), metric("mythpat", 20)])

    def test_report_keeps_publication_disabled(self):
        report = ranking_report([metric("mythpat", 10)])
        self.assertFalse(report["publishing_enabled"])
        self.assertFalse(report["media_download_enabled"])
        self.assertTrue(report["ranking_is_provisional"])


if __name__ == "__main__":
    unittest.main()
