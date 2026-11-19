"""Tests for dry-run and explicitly approved local batch rendering."""

import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.batch_render import parse_approvals, run_batch


class BatchRenderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.csv_path = self.root / "candidates.csv"
        self.media = self.root / "authorized-local.mp4"
        self.media.write_bytes(b"local synthetic media")
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "source_id", "start_seconds", "end_seconds", "renderable",
            ])
            writer.writeheader()
            writer.writerows([
                {"source_id": "demo-a", "start_seconds": "10", "end_seconds": "25", "renderable": "True"},
                {"source_id": "demo-b", "start_seconds": "30", "end_seconds": "50", "renderable": "False"},
                {"source_id": "demo-c", "start_seconds": "60", "end_seconds": "70", "renderable": "true"},
            ])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_parse_approvals(self) -> None:
        self.assertEqual(parse_approvals("1, 3"), {1, 3})

    def test_rejects_empty_or_invalid_approvals(self) -> None:
        for value in ("", "0", "one", "1,0"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_approvals(value)

    def test_dry_run_is_default_and_does_not_call_renderer(self) -> None:
        with patch("backend.app.batch_render.render_clip") as render:
            result = run_batch(self.csv_path, self.media, self.root / "out", {1, 3})
        render.assert_not_called()
        self.assertEqual([item["status"] for item in result], ["planned", "not_approved", "planned"])
        self.assertFalse((self.root / "out").exists())

    def test_non_renderable_candidate_is_blocked_even_if_approved(self) -> None:
        result = run_batch(self.csv_path, self.media, self.root / "out", {2})
        self.assertEqual(result[1]["status"], "blocked")

    def test_execution_requires_rights_confirmation(self) -> None:
        with self.assertRaisesRegex(PermissionError, "rights confirmation"):
            run_batch(self.csv_path, self.media, self.root / "out", {1}, execute=True)

    def test_execution_calls_renderer_only_for_approved_renderable_rows(self) -> None:
        with patch("backend.app.batch_render.render_clip") as render:
            result = run_batch(
                self.csv_path, self.media, self.root / "out", {1, 2, 3},
                execute=True, rights_confirmed=True,
            )
        self.assertEqual(render.call_count, 2)
        self.assertEqual([item["status"] for item in result], ["rendered", "blocked", "rendered"])
        self.assertTrue(all(call.kwargs["rights_confirmed"] for call in render.call_args_list))

    def test_rejects_approval_outside_csv(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside"):
            run_batch(self.csv_path, self.media, self.root / "out", {4})

    def test_rejects_invalid_bounds_in_approved_row(self) -> None:
        rows = list(csv.DictReader(self.csv_path.open(encoding="utf-8")))
        rows[0]["start_seconds"] = "-1"
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        result = run_batch(self.csv_path, self.media, self.root / "out", {1})
        self.assertEqual(result[0]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
