"""Regression coverage for NUL rejection in candidate CSV text."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


class CandidateCsvNulCharacterTests(unittest.TestCase):
    def test_rejects_nul_character_in_optional_field(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,start_seconds,end_seconds,duration_seconds,renderable,notes\\n"
                "authorized-demo,2,8,6,True,unsafe\\x00note\\n",
                encoding="utf-8",
                newline="",
            )

            with self.assertRaisesRegex(ValueError, "candidate CSV could not be read.*NUL"):
                load_selected_candidate(csv_path, 1)


if __name__ == "__main__":
    unittest.main()
