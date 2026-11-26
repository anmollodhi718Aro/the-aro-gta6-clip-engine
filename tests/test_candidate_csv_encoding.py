"""Regression tests for valid spreadsheet-export candidate CSV encoding."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


class CandidateCsvEncodingTests(unittest.TestCase):
    def test_accepts_utf8_bom_and_crlf_candidate_export(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_bytes(
                (
                    "\ufeffsource_id,start_seconds,end_seconds,duration_seconds,renderable\r\n"
                    "authorized-demo,2,8,6,True\r\n"
                ).encode("utf-8")
            )

            selected = load_selected_candidate(csv_path, 1)

            self.assertEqual(
                selected,
                {
                    "row_number": 1,
                    "source_id": "authorized-demo",
                    "start_seconds": 2.0,
                    "end_seconds": 8.0,
                    "duration_seconds": 6.0,
                },
            )

    def test_preserves_non_ascii_creator_source_id(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,start_seconds,end_seconds,duration_seconds,renderable\\n"
                "creator-東京,2,8,6,True\\n",
                encoding="utf-8",
                newline="",
            )

            selected = load_selected_candidate(csv_path, 1)

            self.assertEqual(selected["source_id"], "creator-東京")
            self.assertEqual(selected["start_seconds"], 2.0)
            self.assertEqual(selected["end_seconds"], 8.0)
            self.assertEqual(selected["duration_seconds"], 6.0)


if __name__ == "__main__":
    unittest.main()
