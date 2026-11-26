"""Regression tests for malformed candidate CSV header cells."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


class CandidateCsvBlankHeaderTests(unittest.TestCase):
    def test_rejects_blank_middle_header_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,,start_seconds,end_seconds,duration_seconds,renderable\n"
                "authorized-demo,note,2,8,6,True\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "blank or duplicate column names"):
                load_selected_candidate(csv_path, 1)

    def test_rejects_blank_trailing_header_cell_parsed_as_none(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,start_seconds,end_seconds,duration_seconds,renderable,\n"
                "authorized-demo,2,8,6,True,unused\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "blank or duplicate column names"):
                load_selected_candidate(csv_path, 1)

    def test_rejects_duplicate_header_cells(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,start_seconds,end_seconds,duration_seconds,renderable,source_id\n"
                "authorized-demo,2,8,6,True,other-id\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "blank or duplicate column names"):
                load_selected_candidate(csv_path, 1)

    def test_rejects_whitespace_only_middle_header_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,   ,start_seconds,end_seconds,duration_seconds,renderable\n"
                "authorized-demo,note,2,8,6,True\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "blank or duplicate column names"):
                load_selected_candidate(csv_path, 1)

    def test_rejects_unicode_whitespace_only_header_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,\u00a0,start_seconds,end_seconds,duration_seconds,renderable\\n"
                "authorized-demo,note,2,8,6,True\\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "blank or duplicate column names"):
                load_selected_candidate(csv_path, 1)

    def test_rejects_whitespace_only_trailing_header_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,start_seconds,end_seconds,duration_seconds,renderable,   \n"
                "authorized-demo,2,8,6,True,unused\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "blank or duplicate column names"):
                load_selected_candidate(csv_path, 1)


if __name__ == "__main__":
    unittest.main()
