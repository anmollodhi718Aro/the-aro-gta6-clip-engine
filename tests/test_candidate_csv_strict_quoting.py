"""Regression tests for strict candidate CSV quote parsing."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


class CandidateCsvStrictQuotingTests(unittest.TestCase):
    def test_rejects_characters_after_a_closed_quoted_field(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
                "authorized-demo,2,8,6,True\n"
                'malformed,2,8,6,"True"trailing\n',
                encoding="utf-8",
                newline="",
            )

            with self.assertRaisesRegex(ValueError, "candidate CSV could not be read"):
                load_selected_candidate(csv_path, 1)


if __name__ == "__main__":
    unittest.main()
