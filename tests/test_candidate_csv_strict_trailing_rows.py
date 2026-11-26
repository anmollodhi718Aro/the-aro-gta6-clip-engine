"""Regression tests for strict parsing of trailing candidate CSV rows."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


class CandidateCsvStrictTrailingRowTests(unittest.TestCase):
    def test_rejects_malformed_trailing_row_after_selected_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
                "authorized-demo,2,8,6,True\n"
                'later-row,9,15,6,"unterminated\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "candidate CSV could not be read"):
                load_selected_candidate(csv_path, 1)


if __name__ == "__main__":
    unittest.main()
