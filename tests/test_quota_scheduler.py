"""Tests for the quota-aware multi-source scheduler."""
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.quota_scheduler import QuotaAwareScheduler


class QuotaAwareSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.scheduler = QuotaAwareScheduler(Path(self.temp.name) / "scheduler.sqlite3")
        self.now = datetime(2026, 11, 18, 10, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.temp.cleanup()

    def test_priority_then_due_time_selects_source_and_respects_interval(self):
        self.scheduler.configure_source("low", interval_seconds=30, request_cost_units=5, priority=0, now=self.now)
        self.scheduler.configure_source("high", interval_seconds=60, request_cost_units=5, priority=10, now=self.now)
        claimed = self.scheduler.claim_next(daily_quota_units=100, now=self.now)
        self.assertEqual(claimed.source_id, "high")
        self.assertEqual(claimed.quota_remaining_today, 95)
        second = self.scheduler.claim_next(daily_quota_units=100, now=self.now)
        self.assertEqual(second.source_id, "low")
        self.assertEqual(second.quota_used_today, 10)
        third = self.scheduler.claim_next(daily_quota_units=100, now=self.now + timedelta(seconds=31))
        self.assertEqual(third.source_id, "low")
        self.assertEqual(third.quota_used_today, 15)
        later = self.scheduler.claim_next(daily_quota_units=100, now=self.now + timedelta(seconds=60))
        self.assertEqual(later.source_id, "high")

    def test_daily_quota_never_exceeded_and_resets_utc_day(self):
        self.scheduler.configure_source("a", interval_seconds=1, request_cost_units=7, now=self.now)
        first = self.scheduler.claim_next(daily_quota_units=10, now=self.now)
        self.assertEqual(first.quota_used_today, 7)
        second = self.scheduler.claim_next(daily_quota_units=10, now=self.now + timedelta(seconds=2))
        self.assertIsNone(second)
        next_day = self.scheduler.claim_next(daily_quota_units=10, now=self.now + timedelta(days=1))
        self.assertEqual(next_day.quota_used_today, 7)

    def test_disabled_source_is_not_claimed(self):
        self.scheduler.configure_source("paused", interval_seconds=1, request_cost_units=1, enabled=False, now=self.now)
        self.assertIsNone(self.scheduler.claim_next(daily_quota_units=10, now=self.now))

    def test_expensive_request_waits_if_budget_insufficient(self):
        self.scheduler.configure_source("expensive", interval_seconds=1, request_cost_units=11, now=self.now)
        self.assertIsNone(self.scheduler.claim_next(daily_quota_units=10, now=self.now))
        self.assertEqual(self.scheduler.quota_used(now=self.now), 0)

    def test_configuration_update_preserves_next_due(self):
        self.scheduler.configure_source("a", interval_seconds=10, request_cost_units=2, now=self.now)
        self.scheduler.claim_next(daily_quota_units=10, now=self.now)
        due_before = self.scheduler.list_sources()[0].next_due_at
        self.scheduler.configure_source("a", interval_seconds=20, request_cost_units=3, now=self.now)
        self.assertEqual(self.scheduler.list_sources()[0].next_due_at, due_before)

    def test_rejects_naive_time(self):
        with self.assertRaises(ValueError):
            self.scheduler.claim_next(daily_quota_units=10, now=datetime(2026, 11, 18))

if __name__ == "__main__":
    unittest.main()
