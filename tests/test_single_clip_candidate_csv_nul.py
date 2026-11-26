"""Regression tests for NUL rejection in the single-clip candidate CSV loader."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


class SingleClipCandidateCsvNulTests(unittest.TestCase):
    def _assert_rejected(self, csv_text):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                handle.write(csv_text)
            with self.assertRaisesRegex(
                ValueError, "candidate CSV could not be read: NUL character found"
            ):
                load_selected_candidate(csv_path, 1)

    def test_rejects_nul_in_optional_field(self):
        self._assert_rejected(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable,notes\n"
            "authorized-demo,2,8,6,True,unsafe\\x00note\n".replace("\\x00", "\x00")
        )

    def test_rejects_nul_in_header(self):
        self._assert_rejected(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable,notes\\x00\n"
            "authorized-demo,2,8,6,True,ordinary note\n".replace("\\x00", "\x00")
        )

    def test_rejects_nul_in_unselected_trailing_row(self):
        self._assert_rejected(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable,notes\n"
            "authorized-demo,2,8,6,True,selected row\n"
            "other-demo,10,16,6,True,unsafe\\x00trailing note\n".replace("\\x00", "\x00")
        )

    def test_rejects_nul_inside_multiline_quoted_field(self):
        self._assert_rejected(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable,notes\n"
            'authorized-demo,2,8,6,True,"first line\n'
            'unsafe\\x00second line"\n'.replace("\\x00", "\x00")
        )


if __name__ == "__main__":
    unittest.main()
