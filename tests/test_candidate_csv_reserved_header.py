"""Regression tests for candidate CSV parser edge cases."""

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


class CandidateCsvReservedHeaderTests(unittest.TestCase):
    def test_reserved_looking_header_is_treated_as_user_data(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,start_seconds,end_seconds,duration_seconds,renderable,__aro_extra_fields__\n"
                "authorized-demo,2,8,6,True,operator-note\n",
                encoding="utf-8",
            )
            selected = load_selected_candidate(csv_path, 1)

        self.assertEqual(selected["source_id"], "authorized-demo")
        self.assertEqual(selected["start_seconds"], 2.0)
        self.assertEqual(selected["end_seconds"], 8.0)
        self.assertEqual(selected["duration_seconds"], 6.0)

    def test_extra_cells_still_fail_with_reserved_looking_header(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candidates.csv"
            csv_path.write_text(
                "source_id,start_seconds,end_seconds,duration_seconds,renderable,__aro_extra_fields__\n"
                "authorized-demo,2,8,6,True,operator-note,unexpected\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "more values than its header"):
                load_selected_candidate(csv_path, 1)


if __name__ == "__main__":
    unittest.main()
