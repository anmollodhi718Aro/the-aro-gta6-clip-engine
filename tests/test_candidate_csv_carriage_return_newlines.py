"""Regression coverage for CR-only candidate CSV record and quoted-field newlines."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


class CandidateCsvCarriageReturnNewlineTests(unittest.TestCase):
    def test_accepts_cr_only_records_and_embedded_cr_in_quoted_optional_field(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,start_seconds,end_seconds,duration_seconds,renderable,notes\r"
                'authorized-demo,2,8,6,True,"first line\rsecond line"\r',
                encoding="utf-8",
                newline="",
            )

            candidate = load_selected_candidate(csv_path, 1)

            self.assertEqual(candidate["source_id"], "authorized-demo")
            self.assertEqual(candidate["start_seconds"], 2.0)
            self.assertEqual(candidate["end_seconds"], 8.0)
            self.assertEqual(candidate["duration_seconds"], 6.0)


if __name__ == "__main__":
    unittest.main()
