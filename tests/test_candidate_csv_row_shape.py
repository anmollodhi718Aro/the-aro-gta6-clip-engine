"""Regression tests for malformed candidate CSV data rows."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


HEADER = "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
VALID = "authorized-demo,2,8,6,True\n"


class CandidateCsvRowShapeTests(unittest.TestCase):
    def test_rejects_short_later_row_after_selected_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                HEADER + VALID + "later-candidate,3,9,6\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "candidate row 2 is missing required values"):
                load_selected_candidate(csv_path, 1)

    def test_rejects_extra_cells_in_later_row_after_selected_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                HEADER + VALID + "later-candidate,3,9,6,True,unexpected\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "candidate row 2 has more values than its header"):
                load_selected_candidate(csv_path, 1)

    def test_rejects_unterminated_quote_in_later_row_after_selected_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                HEADER + VALID + 'later-candidate,3,9,6,"unterminated\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "candidate CSV could not be read"):
                load_selected_candidate(csv_path, 1)


if __name__ == "__main__":
    unittest.main()
