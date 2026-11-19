"""Tests for safe render-run directories and atomic reports."""
import json
import tempfile
import unittest
from pathlib import Path

from backend.app.output_manager import (
    create_run_directory, make_run_id, write_json_atomic,
    write_json_no_overwrite, write_texts_no_overwrite,
)


class OutputManagerTests(unittest.TestCase):
    def test_generated_and_explicit_run_ids_are_safe(self):
        self.assertRegex(make_run_id(), r"^[a-f0-9]{32}$")
        self.assertEqual(make_run_id("review-2026_11"), "review-2026_11")

    def test_rejects_path_traversal_and_unsafe_ids(self):
        for value in ("../outside", "..", ".", "has space", "a/b", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                make_run_id(value)

    def test_run_directory_is_unique_and_never_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            first = create_run_directory(temp, "run-1")
            self.assertTrue(first.is_dir())
            with self.assertRaisesRegex(FileExistsError, "already exists"):
                create_run_directory(temp, "run-1")
            self.assertEqual(list(Path(temp).iterdir()), [first])

    def test_atomic_report_round_trips_json(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "nested" / "report.json"
            result = write_json_atomic(target, [{"status": "rendered", "clip": "clip_001.mp4"}])
            self.assertEqual(result, target)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), [
                {"status": "rendered", "clip": "clip_001.mp4"}
            ])
            self.assertEqual(list(target.parent.iterdir()), [target])


    def test_no_overwrite_json_is_valid_and_refuses_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "report.json"
            result = write_json_no_overwrite(target, {"status": "ready"})
            self.assertEqual(result, target)
            raw = target.read_text(encoding="utf-8")
            self.assertTrue(raw.endswith("\n"))
            self.assertEqual(json.loads(raw), {"status": "ready"})
            with self.assertRaises(FileExistsError):
                write_json_no_overwrite(target, {"status": "replaced"})
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"status": "ready"})

    def test_multi_file_no_overwrite_rolls_back_partial_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "new.txt"
            occupied = root / "occupied.txt"
            occupied.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                write_texts_no_overwrite({first: "new", occupied: "replace"})
            self.assertFalse(first.exists())
            self.assertEqual(occupied.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
