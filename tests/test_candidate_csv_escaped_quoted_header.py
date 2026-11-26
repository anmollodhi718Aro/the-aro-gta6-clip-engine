"""Compatibility regression for escaped quotes and commas in candidate CSV headers."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


class CandidateCsvEscapedQuotedHeaderTests(unittest.TestCase):
    def test_accepts_escaped_quote_and_comma_in_optional_header_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                '"source_id","start_seconds","end_seconds","duration_seconds","renderable","notes""label,extra"\n'
                '"authorized-demo",2,8,6,True,"a value with, comma and ""escaped quotes"""\n',
                encoding="utf-8",
                newline="",
            )

            selected = load_selected_candidate(csv_path, 1)

        self.assertEqual(selected["source_id"], "authorized-demo")
        self.assertEqual(selected["start_seconds"], 2.0)
        self.assertEqual(selected["end_seconds"], 8.0)
        self.assertEqual(selected["duration_seconds"], 6.0)


if __name__ == "__main__":
    unittest.main()
