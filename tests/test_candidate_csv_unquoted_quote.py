"""Regression tests for strict candidate CSV quote boundaries."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


HEADER = "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"


class CandidateCsvUnquotedQuoteTests(unittest.TestCase):
    def test_rejects_quote_inside_unquoted_later_field_after_selected_row(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                HEADER
                + "authorized-demo,2,8,6,True\n"
                + 'later-candidate,9,15,6,Tr"ue\n',
                encoding="utf-8",
                newline="",
            )

            with self.assertRaisesRegex(
                ValueError, "candidate CSV could not be read"
            ):
                load_selected_candidate(csv_path, 1)

    def test_accepts_escaped_quotes_inside_a_quoted_source_id(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                HEADER + '"authorized ""demo""",2,8,6,True\n',
                encoding="utf-8",
                newline="",
            )

            candidate = load_selected_candidate(csv_path, 1)

            self.assertEqual(candidate["source_id"], 'authorized "demo"')
            self.assertEqual(candidate["start_seconds"], 2.0)
            self.assertEqual(candidate["end_seconds"], 8.0)


if __name__ == "__main__":
    unittest.main()
