"""Tests for evidence-backed AI chat analytics ledger validation."""
import copy
import json
import unittest
from pathlib import Path

from backend.app.analytics_validation import validate_analytics_ledger


ROOT = Path(__file__).resolve().parents[1]


class AnalyticsValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid_ledger = json.loads(
            (ROOT / "analytics" / "ai_chat_sessions.json").read_text(encoding="utf-8")
        )

    def test_canonical_ledger_is_valid(self):
        self.assertIsNone(validate_analytics_ledger(self.valid_ledger))

    def test_accepts_unknown_metrics_as_null(self):
        ledger = copy.deepcopy(self.valid_ledger)
        session = ledger["sessions"][0]
        session["elapsed_seconds"] = None
        session["active_work_seconds"] = None
        session["score"] = None
        self.assertIsNone(validate_analytics_ledger(ledger))

    def test_rejects_missing_nullable_measurement_fields(self):
        ledger = copy.deepcopy(self.valid_ledger)
        del ledger["sessions"][0]["elapsed_seconds"]
        with self.assertRaisesRegex(ValueError, "missing required fields.*elapsed_seconds"):
            validate_analytics_ledger(ledger)

    def test_rejects_duplicate_chat_ids(self):
        ledger = copy.deepcopy(self.valid_ledger)
        ledger["sessions"].append(copy.deepcopy(ledger["sessions"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate chat_id"):
            validate_analytics_ledger(ledger)

    def test_rejects_invalid_chat_id(self):
        ledger = copy.deepcopy(self.valid_ledger)
        ledger["sessions"][0]["chat_id"] = "CHAT-14"
        with self.assertRaisesRegex(ValueError, "ARO-CHAT-NNNN"):
            validate_analytics_ledger(ledger)

    def test_rejects_weights_that_do_not_sum_to_one(self):
        ledger = copy.deepcopy(self.valid_ledger)
        ledger["scoring_model"]["weights"]["task_importance"] = 0.3
        with self.assertRaisesRegex(ValueError, "sum to 1.0"):
            validate_analytics_ledger(ledger)

    def test_rejects_boolean_as_numeric_measurement(self):
        ledger = copy.deepcopy(self.valid_ledger)
        ledger["sessions"][0]["elapsed_seconds"] = True
        with self.assertRaisesRegex(ValueError, "elapsed_seconds"):
            validate_analytics_ledger(ledger)

    def test_rejects_timezone_free_timestamps(self):
        ledger = copy.deepcopy(self.valid_ledger)
        ledger["sessions"][0]["started_at"] = "2026-11-20T04:51:00"
        with self.assertRaisesRegex(ValueError, "timezone offset"):
            validate_analytics_ledger(ledger)

    def test_rejects_end_time_before_start_time(self):
        ledger = copy.deepcopy(self.valid_ledger)
        ledger["sessions"][0]["ended_at"] = "2026-11-19T00:00:00+05:30"
        with self.assertRaisesRegex(ValueError, "must not precede"):
            validate_analytics_ledger(ledger)

    def test_rejects_invalid_score_range(self):
        ledger = copy.deepcopy(self.valid_ledger)
        ledger["sessions"][0]["score"] = 101
        with self.assertRaisesRegex(ValueError, "score"):
            validate_analytics_ledger(ledger)


if __name__ == "__main__":
    unittest.main()
