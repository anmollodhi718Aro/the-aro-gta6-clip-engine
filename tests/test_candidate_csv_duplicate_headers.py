"""Regression tests for duplicate candidate CSV header names."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


class CandidateCsvDuplicateHeaderTests(unittest.TestCase):
    def test_rejects_duplicate_required_header_before_row_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
                "authorized-demo,shadow-source,2,8,6,True\n",
                encoding="utf-8",
                newline="",
            )

            with self.assertRaisesRegex(ValueError, "duplicate column names"):
                load_selected_candidate(csv_path, 1)


if __name__ == "__main__":
    unittest.main()
