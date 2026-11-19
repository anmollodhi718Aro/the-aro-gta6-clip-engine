"""Tests for explainable candidate review scoring."""
import unittest

from backend.app.candidate_quality import score_candidate, score_rows


class CandidateQualityTests(unittest.TestCase):
    def candidate(self, **updates):
        row = {
            "peak_message_count": 20,
            "duration_seconds": 45,
            "start_seconds": 10,
            "end_seconds": 55,
            "renderable": True,
        }
        row.update(updates)
        return row

    def test_full_score_has_explainable_components(self):
        result = score_candidate(self.candidate())
        self.assertEqual(result["quality_score"], 100)
        self.assertEqual(result["activity_points"], 40)
        self.assertEqual(result["duration_points"], 30)
        self.assertEqual(result["sync_points"], 30)
        self.assertEqual(len(result["quality_reasons"]), 3)

    def test_activity_is_capped_at_twenty_messages(self):
        result = score_candidate(self.candidate(peak_message_count=200))
        self.assertEqual(result["activity_points"], 40)

    def test_duration_penalty_is_transparent(self):
        short = score_candidate(self.candidate(duration_seconds=7.5))
        long = score_candidate(self.candidate(duration_seconds=135))
        self.assertEqual(short["duration_points"], 15)
        self.assertEqual(long["duration_points"], 15)

    def test_unrenderable_candidate_gets_no_alignment_points(self):
        result = score_candidate(self.candidate(renderable=False))
        self.assertEqual(result["sync_points"], 0)
        self.assertIn("not verified", result["quality_reasons"][2])

    def test_invalid_bounds_do_not_claim_alignment(self):
        result = score_candidate(self.candidate(start_seconds=-1))
        self.assertEqual(result["sync_points"], 0)

    def test_rejects_negative_activity(self):
        with self.assertRaisesRegex(ValueError, "negative"):
            score_candidate(self.candidate(peak_message_count=-1))

    def test_rejects_non_finite_duration(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            score_candidate(self.candidate(duration_seconds=float("nan")))

    def test_score_rows_preserves_original_metadata(self):
        row = self.candidate(source_id="demo")
        result = score_rows([row])[0]
        self.assertEqual(result["source_id"], "demo")
        self.assertIn("quality_score", result)


if __name__ == "__main__":
    unittest.main()
