"""Regression tests for multiline and incomplete candidate CSV quoting."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


HEADER = "source_id,start_seconds,end_seconds,duration_seconds,renderable,notes\r\n"


class CandidateCsvMultilineAndUnclosedQuoteTests(unittest.TestCase):
    def test_rejects_unclosed_quote_in_later_row_after_selected_row(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                HEADER
                + 'authorized-demo,2,8,6,True,"valid note"\r\n'
                + 'later-candidate,9,15,6,True,"unfinished note\r\n',
                encoding="utf-8",
                newline="",
            )

            with self.assertRaisesRegex(ValueError, "candidate CSV could not be read"):
                load_selected_candidate(csv_path, 1)

    def test_accepts_embedded_crlf_inside_a_quoted_optional_field(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                HEADER + 'authorized-demo,2,8,6,True,"first line\r\nsecond line"\r\n',
                encoding="utf-8",
                newline="",
            )

            candidate = load_selected_candidate(csv_path, 1)

            self.assertEqual(candidate["source_id"], "authorized-demo")
            self.assertEqual(candidate["duration_seconds"], 6.0)


if __name__ == "__main__":
    unittest.main()
