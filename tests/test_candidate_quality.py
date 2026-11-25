"""Tests for explainable candidate review scoring."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

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

    def test_duration_mismatch_does_not_claim_recording_alignment(self):
        result = score_candidate(self.candidate(end_seconds=90))
        self.assertEqual(result["sync_points"], 0)
        self.assertIn("not verified", result["quality_reasons"][2])

    def test_bounds_over_review_limit_do_not_claim_alignment(self):
        result = score_candidate(self.candidate(
            duration_seconds=181, end_seconds=191
        ))
        self.assertEqual(result["sync_points"], 0)

    def test_boolean_numeric_metadata_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not boolean"):
            score_candidate(self.candidate(peak_message_count=True))

    def test_boolean_clip_bound_is_not_scored_as_numeric(self):
        result = score_candidate(self.candidate(start_seconds=True))
        self.assertEqual(result["sync_points"], 0)


class CandidateQualityCliSafetyTests(unittest.TestCase):
    def _write_candidates(self, path):
        path.write_text(
            "peak_message_count,duration_seconds,start_seconds,end_seconds,renderable\\n"
            "20,45,10,55,true\\n",
            encoding="utf-8",
        )

    def test_cli_refuses_to_overwrite_input_even_via_relative_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "candidates.csv"
            self._write_candidates(source)
            original = source.read_text(encoding="utf-8")
            with patch("sys.argv", [
                "candidate_quality", str(source),
                "--output", str(source.parent / "." / source.name),
            ]):
                from backend.app.candidate_quality import main
                self.assertEqual(main(), 2)
            self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_cli_refuses_to_overwrite_existing_review_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "candidates.csv"
            output = Path(directory) / "scored.csv"
            self._write_candidates(source)
            output.write_text("keep-this-review\\n", encoding="utf-8")
            with patch("sys.argv", [
                "candidate_quality", str(source), "--output", str(output),
            ]):
                from backend.app.candidate_quality import main
                self.assertEqual(main(), 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep-this-review\\n")


if __name__ == "__main__":
    unittest.main()
