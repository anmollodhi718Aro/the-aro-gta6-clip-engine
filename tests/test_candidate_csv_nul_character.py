"""Regression coverage for NUL rejection throughout candidate CSV input."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


class CandidateCsvNulCharacterTests(unittest.TestCase):
    def _assert_csv_rejected_for_nul(self, csv_text, row_number=1):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(csv_text, encoding="utf-8", newline="")

            with self.assertRaisesRegex(ValueError, "candidate CSV could not be read.*NUL"):
                load_selected_candidate(csv_path, row_number)

    def test_rejects_nul_character_in_optional_field(self):
        self._assert_csv_rejected_for_nul(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable,notes\n"
            "authorized-demo,2,8,6,True,unsafe\x00note\n"
        )

    def test_rejects_nul_character_in_header(self):
        self._assert_csv_rejected_for_nul(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable,notes\x00\n"
            "authorized-demo,2,8,6,True,ordinary note\n"
        )

    def test_rejects_nul_character_in_unselected_trailing_row(self):
        self._assert_csv_rejected_for_nul(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable,notes\n"
            "authorized-demo,2,8,6,True,selected row\n"
            "other-demo,10,16,6,True,unsafe\x00trailing note\n"
        )


    def test_rejects_nul_character_inside_multiline_quoted_field(self):
        self._assert_csv_rejected_for_nul(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable,notes\n"
            'authorized-demo,2,8,6,True,"first line\n'
            'unsafe\x00second line"\n'
        )


if __name__ == "__main__":
    unittest.main()
