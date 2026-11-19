"""Tests for dry-run and explicitly approved local batch rendering."""

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.batch_render import load_failed_rows, parse_approvals, run_batch


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
                execute=True, rights_confirmed=True, media_duration_seconds=100.0,
            )
        self.assertEqual(render.call_count, 2)
        self.assertEqual([item["status"] for item in result], ["rendered", "blocked", "rendered"])
        self.assertTrue(all(call.kwargs["rights_confirmed"] for call in render.call_args_list))

    def test_vertical_option_is_forwarded_to_renderer(self) -> None:
        with patch("backend.app.batch_render.render_clip") as render:
            result = run_batch(
                self.csv_path, self.media, self.root / "out", {1},
                execute=True, rights_confirmed=True, media_duration_seconds=100.0,
                vertical=True,
            )
        self.assertEqual(result[0]["status"], "rendered")
        self.assertTrue(render.call_args.kwargs["vertical"])

    def test_each_execution_uses_a_new_run_folder(self) -> None:
        with patch("backend.app.batch_render.render_clip"):
            first = run_batch(self.csv_path, self.media, self.root / "out", {1},
                              execute=True, rights_confirmed=True, media_duration_seconds=100.0, run_id="run-one")
            second = run_batch(self.csv_path, self.media, self.root / "out", {1},
                               execute=True, rights_confirmed=True, media_duration_seconds=100.0, run_id="run-two")
        self.assertIn("run-one", first[0]["output_path"])
        self.assertIn("run-two", second[0]["output_path"])
        self.assertNotEqual(first[0]["output_path"], second[0]["output_path"])

    def test_existing_run_folder_is_never_reused(self) -> None:
        with patch("backend.app.batch_render.render_clip"):
            run_batch(self.csv_path, self.media, self.root / "out", {1},
                      execute=True, rights_confirmed=True, media_duration_seconds=100.0, run_id="same-run")
            with self.assertRaisesRegex(FileExistsError, "already exists"):
                run_batch(self.csv_path, self.media, self.root / "out", {1},
                          execute=True, rights_confirmed=True, media_duration_seconds=100.0, run_id="same-run")

    def test_rejects_unsafe_run_id(self) -> None:
        with self.assertRaises(ValueError):
            run_batch(self.csv_path, self.media, self.root / "out", {1}, run_id="../escape")

    def _write_retry_report(self, rows):
        path = self.root / "previous-report.json"
        path.write_text(json.dumps(rows), encoding="utf-8")
        return path

    def test_retry_selects_only_failed_rows_with_matching_source_data(self) -> None:
        report = self._write_retry_report([
            {"candidate_row": 1, "source_id": "demo-a", "start_seconds": 10.0, "end_seconds": 25.0, "status": "failed"},
            {"candidate_row": 2, "source_id": "demo-b", "start_seconds": 30.0, "end_seconds": 50.0, "status": "blocked"},
            {"candidate_row": 3, "source_id": "demo-c", "start_seconds": 60.0, "end_seconds": 70.0, "status": "rendered"},
        ])
        self.assertEqual(load_failed_rows(report, self.csv_path), {1})

    def test_retry_rejects_changed_candidate_bounds(self) -> None:
        report = self._write_retry_report([
            {"candidate_row": 1, "source_id": "demo-a", "start_seconds": 9.0, "end_seconds": 25.0, "status": "failed"},
        ])
        with self.assertRaisesRegex(ValueError, "bounds changed"):
            load_failed_rows(report, self.csv_path)

    def test_retry_rejects_changed_source_identity(self) -> None:
        report = self._write_retry_report([
            {"candidate_row": 1, "source_id": "different-source", "start_seconds": 10.0, "end_seconds": 25.0, "status": "failed"},
        ])
        with self.assertRaisesRegex(ValueError, "no longer matches"):
            load_failed_rows(report, self.csv_path)

    def test_retry_rejects_reports_without_failed_rows(self) -> None:
        report = self._write_retry_report([
            {"candidate_row": 1, "source_id": "demo-a", "start_seconds": 10.0, "end_seconds": 25.0, "status": "rendered"},
        ])
        with self.assertRaisesRegex(ValueError, "no safely retryable"):
            load_failed_rows(report, self.csv_path)

    def test_retry_checks_exact_local_media_identity_when_media_is_supplied(self) -> None:
        stat = self.media.stat()
        identity = {
            "path": str(self.media.resolve()),
            "size_bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }
        report = self._write_retry_report([
            {
                "candidate_row": 1, "source_id": "demo-a",
                "start_seconds": 10.0, "end_seconds": 25.0,
                "status": "failed", "media_identity": identity,
            },
        ])
        self.assertEqual(load_failed_rows(report, self.csv_path, self.media), {1})

        identity["size_bytes"] += 1
        report = self._write_retry_report([
            {
                "candidate_row": 1, "source_id": "demo-a",
                "start_seconds": 10.0, "end_seconds": 25.0,
                "status": "failed", "media_identity": identity,
            },
        ])
        with self.assertRaisesRegex(ValueError, "media file changed or differs"):
            load_failed_rows(report, self.csv_path, self.media)

    def test_retry_rejects_legacy_report_without_media_identity(self) -> None:
        report = self._write_retry_report([
            {
                "candidate_row": 1, "source_id": "demo-a",
                "start_seconds": 10.0, "end_seconds": 25.0,
                "status": "failed",
            },
        ])
        with self.assertRaisesRegex(ValueError, "does not record local media identity"):
            load_failed_rows(report, self.csv_path, self.media)

    def test_retry_rejects_legacy_failure_without_recorded_bounds(self) -> None:
        report = self._write_retry_report([
            {"candidate_row": 1, "source_id": "demo-a", "status": "failed"},
        ])
        with self.assertRaisesRegex(ValueError, "lacks valid measured bounds"):
            load_failed_rows(report, self.csv_path)

    def test_retry_runs_only_failed_rows_from_previous_report(self) -> None:
        report = self._write_retry_report([
            {"candidate_row": 1, "source_id": "demo-a", "start_seconds": 10.0, "end_seconds": 25.0, "status": "failed"},
            {"candidate_row": 3, "source_id": "demo-c", "start_seconds": 60.0, "end_seconds": 70.0, "status": "rendered"},
        ])
        selected = load_failed_rows(report, self.csv_path)
        with patch("backend.app.batch_render.render_clip") as render:
            result = run_batch(self.csv_path, self.media, self.root / "retry-out", selected,
                               execute=True, rights_confirmed=True, media_duration_seconds=100.0, run_id="retry-one")
        self.assertEqual(render.call_count, 1)
        self.assertEqual([row["status"] for row in result], ["rendered", "not_approved", "not_approved"])


    def test_execution_blocks_clip_past_actual_media_duration(self) -> None:
        with patch("backend.app.batch_render.render_clip") as render:
            result = run_batch(
                self.csv_path, self.media, self.root / "out", {3},
                execute=True, rights_confirmed=True, media_duration_seconds=65.0,
            )
        render.assert_not_called()
        self.assertEqual(result[2]["status"], "failed")
        self.assertIn("beyond actual media duration", result[2]["message"])

    def test_execution_rejects_invalid_media_duration(self) -> None:
        for duration in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(duration=duration), self.assertRaisesRegex(ValueError, "finite positive"):
                run_batch(
                    self.csv_path, self.media, self.root / "out", {1},
                    execute=True, rights_confirmed=True, media_duration_seconds=duration,
                )

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
