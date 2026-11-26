"""Regression tests for malformed quoting in candidate CSV headers."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


class CandidateCsvMalformedHeaderQuoteTests(unittest.TestCase):
    def _assert_header_rejected(self, header):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                header
                + "\n"
                + "authorized-demo,2,8,6,True\n",
                encoding="utf-8",
                newline="",
            )

            with self.assertRaisesRegex(ValueError, "candidate CSV could not be read"):
                load_selected_candidate(csv_path, 1)

    def test_rejects_quote_inside_unquoted_header_cell(self):
        self._assert_header_rejected(
            'source_id",start_seconds,end_seconds,duration_seconds,renderable'
        )

    def test_rejects_trailing_text_after_quoted_header_cell(self):
        self._assert_header_rejected(
            '"source_id"trailing,start_seconds,end_seconds,duration_seconds,renderable'
        )


if __name__ == "__main__":
    unittest.main()
