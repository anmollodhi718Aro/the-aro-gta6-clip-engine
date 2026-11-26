"""Regression coverage for CSV overflow-key/header collisions."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app.single_clip_render import load_selected_candidate


class CandidateCsvOverflowKeyCollisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.csv_path = Path(self.temp_dir.name) / "candidates.csv"

    def test_user_header_matching_old_overflow_key_is_ordinary_column(self) -> None:
        self.csv_path.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable,"
            "__aro_extra_fields__\\n"
            "authorized-demo,1,5,4,True,user-owned-value\\n",
            encoding="utf-8",
        )

        selected = load_selected_candidate(self.csv_path, 1)

        self.assertEqual(selected["source_id"], "authorized-demo")
        self.assertEqual(selected["start_seconds"], 1.0)
        self.assertEqual(selected["end_seconds"], 5.0)

    def test_true_overflow_cells_still_fail_with_collision_header_present(self) -> None:
        self.csv_path.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable,"
            "__aro_extra_fields__\\n"
            "authorized-demo,1,5,4,True,user-owned-value,unexpected-extra\\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "more values than its header"):
            load_selected_candidate(self.csv_path, 1)


if __name__ == "__main__":
    unittest.main()
