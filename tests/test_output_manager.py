"""Tests for safe render-run directories and atomic reports."""
import json
import tempfile
import unittest
from pathlib import Path

from backend.app.output_manager import (\n    create_run_directory, make_run_id, write_json_atomic,\n    write_json_no_overwrite, write_texts_no_overwrite,\n)


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

    def test_text_bundle_publishes_all_files_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "draft.md"
            second = Path(temp) / "draft.json"
            result = write_texts_no_overwrite({first: "# draft\\n", second: "{\\n  \"ok\": true\\n}\\n"})
            self.assertEqual(result, (first, second))
            self.assertEqual(first.read_text(encoding="utf-8"), "# draft\\n")
            self.assertIn('"ok": true', second.read_text(encoding="utf-8"))
            with self.assertRaises(FileExistsError):
                write_texts_no_overwrite({first: "replacement"})
            self.assertEqual(first.read_text(encoding="utf-8"), "# draft\\n")

    def test_text_bundle_rolls_back_only_its_own_partial_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "new.md"
            second = Path(temp) / "existing.json"
            second.write_text("keep this", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                write_texts_no_overwrite({first: "new draft", second: "replacement"})
            self.assertFalse(first.exists())
            self.assertEqual(second.read_text(encoding="utf-8"), "keep this")
            self.assertEqual(sorted(path.name for path in Path(temp).iterdir()), ["existing.json"])

    def test_json_no_overwrite_preserves_existing_report(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "report.json"
            target.write_text("owner data", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                write_json_no_overwrite(target, {"replacement": True})
            self.assertEqual(target.read_text(encoding="utf-8"), "owner data")

    def test_atomic_report_round_trips_json(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "nested" / "report.json"
            result = write_json_atomic(target, [{"status": "rendered", "clip": "clip_001.mp4"}])
            self.assertEqual(result, target)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), [
                {"status": "rendered", "clip": "clip_001.mp4"}
            ])
            self.assertEqual(list(target.parent.iterdir()), [target])


if __name__ == "__main__":
    unittest.main()
