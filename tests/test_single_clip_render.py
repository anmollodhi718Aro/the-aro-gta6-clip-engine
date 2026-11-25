"""Tests for the one-selected-video clip render path."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.clip_pack import write_clip_pack
from backend.app.single_clip_render import (
    _create_stable_source_snapshot, load_selected_candidate, main, render_selected_clip,
)


PASS = {"status": "PASS", "duration_seconds": 20.0, "video_streams": [{"codec": "h264"}]}


class SingleClipRenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "selected.mp4"
        self.source.write_bytes(b"synthetic video")
        self.output = self.root / "clip.mp4"

    def tearDown(self):
        self.temp.cleanup()

    def test_loads_exact_selected_review_ready_candidate(self):
        pack = self.root / "candidates.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,12.5,27.5,15.0,True\n",
            encoding="utf-8",
        )
        selected = load_selected_candidate(pack, 1)
        self.assertEqual(selected["source_id"], "authorized-demo")
        self.assertEqual(selected["start_seconds"], 12.5)
        self.assertEqual(selected["end_seconds"], 27.5)
        self.assertEqual(selected["row_number"], 1)

    def test_clip_pack_export_connects_to_exact_renderer_candidate_loader(self):
        row = {
            "source_id": "authorized-demo",
            "score": 80,
            "peak_message_count": 24,
            "peak_window_start": "2026-11-19T12:00:40+00:00",
            "clip_start_utc": "2026-11-19T12:00:30+00:00",
            "clip_end_utc": "2026-11-19T12:00:45+00:00",
            "start_seconds": 30.0,
            "end_seconds": 45.0,
            "duration_seconds": 15.0,
            "renderable": True,
            "sync_method": "measured_single_origin",
            "sync_max_residual_seconds": 0.0,
            "sync_drift_ppm": 0.0,
            "review_note": "ready for human review",
        }
        csv_path, _ = write_clip_pack([row], self.root / "clip-pack")
        selected = load_selected_candidate(csv_path, 1)
        self.assertEqual(selected["source_id"], row["source_id"])
        self.assertEqual(selected["start_seconds"], row["start_seconds"])
        self.assertEqual(selected["end_seconds"], row["end_seconds"])
        self.assertEqual(selected["duration_seconds"], row["duration_seconds"])


    def test_candidate_selection_rejects_unrenderable_row(self):
        pack = self.root / "candidates.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,12,27,15,False\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "not marked renderable"):
            load_selected_candidate(pack, 1)

    def test_candidate_selection_rejects_duration_mismatch(self):
        pack = self.root / "candidates.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,12,27,14,True\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "duration does not match"):
            load_selected_candidate(pack, 1)

    def test_candidate_selection_rejects_missing_source_identity(self):
        pack = self.root / "candidates.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            ",12,27,15,True\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "no source_id"):
            load_selected_candidate(pack, 1)

    def test_candidate_selection_rejects_nonexistent_row(self):
        pack = self.root / "candidates.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "does not exist"):
            load_selected_candidate(pack, 1)

    def test_cli_uses_explicit_reviewed_candidate_row(self):
        pack = self.root / "candidates.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,12.5,27.5,15.0,True\n",
            encoding="utf-8",
        )
        report_path = self.root / "report.json"
        with patch("sys.argv", [
            "single_clip_render", str(self.source),
            "--candidate-csv", str(pack), "--candidate-row", "1",
            "--output", str(self.output), "--report", str(report_path),
        ]):
            with patch(
                "backend.app.single_clip_render.render_selected_clip",
                return_value={
                    "status": "PLANNED", "start_seconds": 12.5, "end_seconds": 27.5,
                    "upload_performed": False, "publishing_enabled": False,
                },
            ) as render:
                self.assertEqual(main(), 0)
        self.assertEqual(render.call_args.args[2:4], (12.5, 27.5))
        saved = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["candidate_selection"]["source_id"], "authorized-demo")
        self.assertEqual(saved["candidate_selection"]["row_number"], 1)

    def test_dry_run_reports_path_resolution_runtime_error(self):
        with patch("pathlib.Path.resolve", side_effect=RuntimeError("symlink loop")):
            report = render_selected_clip(self.source, self.output, 1, 4)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("output path could not be validated", report["error"])
        self.assertFalse(report["processing_started"])

    def test_cli_handles_path_resolution_runtime_error_without_leaving_report(self):
        report_path = self.root / "report.json"
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]):
            with patch("pathlib.Path.resolve", side_effect=RuntimeError("symlink loop")):
                self.assertEqual(main(), 2)
        self.assertFalse(report_path.exists())

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_dry_run_plans_exactly_one_clip_without_rendering(self, preflight):
        with patch("backend.app.single_clip_render.render_clip") as render:
            report = render_selected_clip(self.source, self.output, 2, 8)
        self.assertEqual(report["status"], "PLANNED")
        self.assertFalse(report["processing_started"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        render.assert_not_called()
        preflight.assert_called_once()
        inspected_source = preflight.call_args.args[0]
        self.assertEqual(inspected_source, self.source)
        self.assertFalse(report["source_snapshot_verified"])
        self.assertFalse(report["source_snapshot_created"])

    def test_dry_run_rejects_invalid_bounds_before_ffprobe(self):
        with patch("backend.app.single_clip_render.inspect_one_video") as preflight:
            report = render_selected_clip(self.source, self.output, "not-a-time", 4)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("clip bounds must be finite numbers", report["error"])
        self.assertFalse(report["processing_started"])
        preflight.assert_not_called()

    def test_rejects_unrepresentable_source_duration_without_crashing(self):
        invalid_preflight = {
            "status": "PASS",
            "duration_seconds": 10 ** 400,
            "video_streams": [{"codec": "h264"}],
        }
        with patch("backend.app.single_clip_render.inspect_one_video", return_value=invalid_preflight):
            with patch("backend.app.single_clip_render.render_clip") as render:
                report = render_selected_clip(self.source, self.output, 2, 8)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["error"], "source preflight did not provide a valid media duration")
        self.assertFalse(report["processing_started"])
        render.assert_not_called()

    def test_rejects_unrepresentable_rendered_duration_without_crashing(self):
        invalid_rendered_preflight = {
            "status": "PASS",
            "duration_seconds": 10 ** 400,
            "video_streams": [{"codec": "h264"}],
        }
        with patch(
            "backend.app.single_clip_render.inspect_one_video",
            side_effect=[PASS, invalid_rendered_preflight],
        ):
            with patch(
                "backend.app.single_clip_render.render_clip",
                return_value=self.output.resolve(),
            ) as render:
                report = render_selected_clip(
                    self.source, self.output, 2, 8,
                    execute=True, rights_confirmed=True,
                )
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(
            report["error"],
            "rendered output duration is outside the expected clip bounds",
        )
        self.assertTrue(report["processing_started"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        render.assert_called_once()


    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_dry_run_never_creates_a_source_snapshot(self, _preflight):
        with patch("backend.app.single_clip_render._create_stable_source_snapshot") as snapshot:
            report = render_selected_clip(self.source, self.output, 2, 8)
        self.assertEqual(report["status"], "PLANNED")
        self.assertFalse(report["source_snapshot_created"])
        snapshot.assert_not_called()

    def test_invalid_clip_bounds_fail_before_source_snapshot(self):
        invalid_bounds = [
            (True, 4),
            (1, False),
            ("not-a-time", 4),
            (1, "not-a-time"),
            (10 ** 10000, 10 ** 10000 + 1),
            (float("inf"), 4),
            (-1, 4),
            (4, 4),
            (1, 182),
        ]
        for start, end in invalid_bounds:
            with self.subTest(start_type=type(start).__name__, end_type=type(end).__name__):
                with patch("backend.app.single_clip_render._create_stable_source_snapshot") as snapshot:
                    with patch("backend.app.single_clip_render.inspect_one_video") as preflight:
                        report = render_selected_clip(
                            self.source, self.output, start, end,
                            execute=True, rights_confirmed=True,
                        )
                self.assertEqual(report["status"], "FAIL")
                self.assertFalse(report["processing_started"])
                self.assertFalse(report["source_snapshot_created"])
                snapshot.assert_not_called()
                preflight.assert_not_called()

    def test_refuses_source_mutation_during_preflight(self):
        def mutate_selected_source(path, *, ffprobe_binary):
            path.write_bytes(b"replacement video bytes")
            return PASS

        with patch("backend.app.single_clip_render.inspect_one_video", side_effect=mutate_selected_source):
            with patch("backend.app.single_clip_render.render_clip") as render:
                report = render_selected_clip(self.source, self.output, 2, 8, execute=True, rights_confirmed=True)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("changed during preflight", report["error"])
        self.assertFalse(report["processing_started"])
        self.assertFalse(report["source_identity_verified"])
        render.assert_not_called()

    def test_execution_rejects_existing_output_before_source_snapshot(self):
        self.output.write_bytes(b"preserve existing output")
        with patch("backend.app.single_clip_render._create_stable_source_snapshot") as snapshot:
            report = render_selected_clip(
                self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("never overwritten", report["error"])
        self.assertFalse(report["processing_started"])
        self.assertFalse(report["source_snapshot_created"])
        snapshot.assert_not_called()
        self.assertEqual(self.output.read_bytes(), b"preserve existing output")

    def test_execution_rejects_symlink_output_before_source_snapshot(self):
        target = self.root / "redirected.mp4"
        try:
            self.output.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable on this runner")
        with patch("backend.app.single_clip_render._create_stable_source_snapshot") as snapshot:
            report = render_selected_clip(
                self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("symbolic link", report["error"])
        self.assertFalse(report["processing_started"])
        snapshot.assert_not_called()
        self.assertFalse(target.exists())
        self.assertTrue(self.output.is_symlink())

    def test_execution_requires_rights_confirmation_before_snapshot(self):
        with patch("backend.app.single_clip_render._create_stable_source_snapshot") as snapshot:
            report = render_selected_clip(self.source, self.output, 2, 8, execute=True)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["processing_started"])
        self.assertFalse(report["source_snapshot_created"])
        snapshot.assert_not_called()

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    @patch("backend.app.single_clip_render.render_clip")
    def test_preflight_and_renderer_consume_the_same_snapshot(self, render, preflight):
        render.side_effect = lambda *args, **kwargs: (self.output.write_bytes(b"rendered mp4"), self.output.resolve())[1]
        preflight.side_effect = [PASS, {"status": "PASS", "duration_seconds": 6.0}]
        report = render_selected_clip(
            self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "RENDERED")
        inspected_path = preflight.call_args_list[0].args[0]
        rendered_path = render.call_args.args[0]
        self.assertEqual(inspected_path, rendered_path)
        self.assertNotEqual(inspected_path, self.source)
        self.assertTrue(report["source_snapshot_verified"])

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    @patch("backend.app.single_clip_render.render_clip")
    def test_renders_one_clip_and_verifies_output(self, render, preflight):
        rendered = self.output.resolve()
        render.return_value = rendered
        preflight.side_effect = [PASS, {"status": "PASS", "duration_seconds": 6.0}]
        report = render_selected_clip(
            self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "RENDERED")
        self.assertTrue(report["processing_started"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        render.assert_called_once()
        self.assertEqual(preflight.call_count, 2)

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_rejects_end_beyond_selected_source_duration(self, _preflight):
        report = render_selected_clip(self.source, self.output, 15, 21)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("exceeds", report["error"])

    @patch("backend.app.single_clip_render.inspect_one_video", return_value={"status": "FAIL", "error": "bad input"})
    def test_rejects_source_that_fails_preflight(self, preflight):
        report = render_selected_clip(self.source, self.output, 1, 4)
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["processing_started"])
        preflight.assert_called_once()

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_rejects_invalid_and_overlong_bounds(self, _preflight):
        for start, end in ((-1, 2), (4, 4), (0, 181), (float("nan"), 3)):
            with self.subTest(start=start, end=end):
                report = render_selected_clip(self.source, self.output, start, end)
                self.assertEqual(report["status"], "FAIL")

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    @patch("backend.app.single_clip_render.render_clip")
    def test_rejects_unexpectedly_short_rendered_output(self, render, preflight):
        render.side_effect = lambda *args, **kwargs: (self.output.write_bytes(b"rendered mp4"), self.output.resolve())[1]
        preflight.side_effect = [PASS, {"status": "PASS", "duration_seconds": 1.0}]
        report = render_selected_clip(
            self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("expected clip bounds", report["error"])

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    @patch("backend.app.single_clip_render.render_clip")
    def test_rejects_nearly_empty_output_for_short_clip(self, render, preflight):
        render.side_effect = lambda *args, **kwargs: (self.output.write_bytes(b"rendered mp4"), self.output.resolve())[1]
        preflight.side_effect = [PASS, {"status": "PASS", "duration_seconds": 0.01}]
        report = render_selected_clip(
            self.source, self.output, 2, 2.1, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("expected clip bounds", report["error"])

    @patch("backend.app.single_clip_render.inspect_one_video")
    @patch("backend.app.single_clip_render.render_clip")
    def test_preserves_own_unverified_output_for_manual_cleanup(self, render, preflight):
        payload = b"unverified render"
        render.side_effect = lambda *args, **kwargs: (
            self.output.write_bytes(payload) and self.output.resolve()
        )
        preflight.side_effect = [PASS, {"status": "FAIL", "error": "invalid output"}]
        with patch.object(Path, "unlink", wraps=Path.unlink) as unlink:
            report = render_selected_clip(
                self.source, self.output, 1, 5, execute=True, rights_confirmed=True,
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["unverified_output_removed"])
        self.assertTrue(report["manual_cleanup_required"])
        self.assertEqual(self.output.read_bytes(), payload)
        unlink.assert_not_called()

    @patch("backend.app.single_clip_render.inspect_one_video")
    @patch("backend.app.single_clip_render.render_clip")
    def test_preserves_replaced_output_when_post_render_ffprobe_fails(self, render, preflight):
        replacement = b"replacement must not be deleted"
        def render_own_file(*args, **kwargs):
            self.output.write_bytes(b"our unverified render")
            return self.output.resolve()
        def replace_during_verification(path, **kwargs):
            original_output = self.root / "original-unverified.mp4"
            self.output.rename(original_output)
            self.output.write_bytes(replacement)
            return {"status": "FAIL", "error": "invalid output"}
        render.side_effect = render_own_file
        preflight.side_effect = [PASS, replace_during_verification]
        report = render_selected_clip(
            self.source, self.output, 1, 5, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["unverified_output_removed"])
        self.assertEqual(self.output.read_bytes(), replacement)

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    @patch("backend.app.single_clip_render.render_clip")
    def test_rejects_output_that_fails_post_render_verification(self, render, preflight):
        render.side_effect = lambda *args, **kwargs: (self.output.write_bytes(b"rendered mp4"), self.output.resolve())[1]
        preflight.side_effect = [PASS, {"status": "FAIL", "error": "invalid output"}]
        report = render_selected_clip(
            self.source, self.output, 1, 5, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("FFprobe verification", report["error"])

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_rejects_same_source_and_non_mp4_output_paths(self, _preflight):
        same = render_selected_clip(self.source, self.source, 1, 4)
        wrong_extension = render_selected_clip(self.source, self.root / "clip.mov", 1, 4)
        self.assertEqual(same["status"], "FAIL")
        self.assertIn("differ", same["error"])
        self.assertEqual(wrong_extension["status"], "FAIL")
        self.assertIn(".mp4", wrong_extension["error"])

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_refuses_existing_output_even_during_dry_run(self, _preflight):
        self.output.write_bytes(b"preserve me")
        report = render_selected_clip(self.source, self.output, 1, 4)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("never overwritten", report["error"])
        self.assertEqual(self.output.read_bytes(), b"preserve me")

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_dry_run_rejects_dangling_symlink_output(self, preflight):
        target = self.root / "redirected.mp4"
        try:
            self.output.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable on this runner")
        report = render_selected_clip(self.source, self.output, 1, 4)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("symbolic link", report["error"])
        self.assertFalse(target.exists())
        preflight.assert_not_called()

    def test_cli_existing_report_blocks_before_render_and_preserves_file(self):
        report_path = self.root / "report.json"
        report_path.write_text("keep this report", encoding="utf-8")
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
            "--execute", "--confirm-rights",
        ]):
            with patch("backend.app.single_clip_render.render_selected_clip") as render:
                self.assertEqual(main(), 2)
        render.assert_not_called()
        self.assertEqual(report_path.read_text(encoding="utf-8"), "keep this report")
        self.assertFalse(self.output.exists())

    def test_cli_report_path_cannot_alias_source_or_output(self):
        for report_path in (self.source, self.output):
            with self.subTest(report_path=report_path):
                with patch("sys.argv", [
                    "single_clip_render", str(self.source), "--start", "1", "--end", "5",
                    "--output", str(self.output), "--report", str(report_path),
                    "--execute", "--confirm-rights",
                ]):
                    with patch("backend.app.single_clip_render.render_selected_clip") as render:
                        self.assertEqual(main(), 2)
                render.assert_not_called()
                self.assertFalse(self.output.exists())

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_cli_writes_exclusive_dry_run_report(self, _preflight):
        report_path = self.root / "report.json"
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]):
            self.assertEqual(main(), 0)
        self.assertTrue(report_path.is_file())
        report_text = report_path.read_text(encoding="utf-8")
        self.assertTrue(report_text.endswith("\n"))
        self.assertEqual(json.loads(report_text)["status"], "PLANNED")
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]):
            self.assertEqual(main(), 2)


    def test_cli_handles_path_resolution_value_error_without_leaving_report(self):
        report_path = self.root / "report.json"
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]):
            with patch("pathlib.Path.resolve", side_effect=ValueError("invalid path")):
                self.assertEqual(main(), 2)
        self.assertFalse(report_path.exists())

    def test_snapshot_fails_closed_on_in_place_mutation_during_copy(self):
        source = self.root / "changing-source.mp4"
        snapshot = self.root / "snapshot.mp4"
        source.write_bytes(b"A" * (2 * 1024 * 1024))
        real_fdopen = __import__("os").fdopen

        class MutatingReader:
            def __init__(self, handle):
                self.handle = handle
                self.changed = False

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                self.handle.close()

            def read(self, size=-1):
                data = self.handle.read(size)
                if not self.changed:
                    self.changed = True
                    source.write_bytes(b"B" * (2 * 1024 * 1024))
                return data

        def fdopen_and_mutate(descriptor, mode):
            return MutatingReader(real_fdopen(descriptor, mode))

        with patch("backend.app.single_clip_render.os.fdopen", side_effect=fdopen_and_mutate):
            with self.assertRaisesRegex(RuntimeError, "changed while its stable snapshot was copied"):
                _create_stable_source_snapshot(source, snapshot)

        self.assertFalse(snapshot.exists())
        self.assertEqual(source.read_bytes(), b"B" * (2 * 1024 * 1024))

    def test_snapshot_rejects_symlink_source_before_creating_snapshot(self):
        target = self.root / "actual-source.mp4"
        selected = self.root / "selected-link.mp4"
        snapshot = self.root / "snapshot.mp4"
        target.write_bytes(b"authorized source bytes")
        try:
            selected.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable on this runner")

        with self.assertRaisesRegex(ValueError, "regular non-symlink"):
            _create_stable_source_snapshot(selected, snapshot)

        self.assertFalse(snapshot.exists())
        self.assertTrue(selected.is_symlink())


    def test_snapshot_fails_closed_when_selected_path_is_replaced_during_copy(self):
        source = self.root / "replaced-source.mp4"
        original = self.root / "original-source.mp4"
        replacement = self.root / "replacement-source.mp4"
        snapshot = self.root / "snapshot-replaced.mp4"
        original_bytes = b"original selected bytes" * 100
        replacement_bytes = b"replacement bytes must not be accepted"
        source.write_bytes(original_bytes)
        replacement.write_bytes(replacement_bytes)
        real_fdopen = __import__("os").fdopen

        class ReplacingReader:
            def __init__(self, handle):
                self.handle = handle
                self.replaced = False

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                self.handle.close()

            def read(self, size=-1):
                data = self.handle.read(size)
                if not self.replaced:
                    self.replaced = True
                    source.rename(original)
                    replacement.rename(source)
                return data

        def fdopen_and_replace(descriptor, mode):
            return ReplacingReader(real_fdopen(descriptor, mode))

        with patch("backend.app.single_clip_render.os.fdopen", side_effect=fdopen_and_replace):
            with self.assertRaisesRegex(RuntimeError, "changed while its stable snapshot was copied"):
                _create_stable_source_snapshot(source, snapshot)

        self.assertFalse(snapshot.exists())
        self.assertEqual(original.read_bytes(), original_bytes)
        self.assertEqual(source.read_bytes(), replacement_bytes)


    def test_snapshot_refuses_source_destination_alias_without_deleting_source(self):
        source = self.root / "same-file.mp4"
        original = b"do not delete the selected source"
        source.write_bytes(original)

        with self.assertRaisesRegex(ValueError, "destination must differ"):
            _create_stable_source_snapshot(source, source)

        self.assertEqual(source.read_bytes(), original)

    def test_snapshot_preserves_preexisting_destination_on_exclusive_create_failure(self):
        source = self.root / "snapshot-source.mp4"
        snapshot = self.root / "already-existing-snapshot.mp4"
        source.write_bytes(b"selected source")
        existing = b"pre-existing destination must survive"
        snapshot.write_bytes(existing)

        with self.assertRaises(FileExistsError):
            _create_stable_source_snapshot(source, snapshot)

        self.assertEqual(snapshot.read_bytes(), existing)
        self.assertEqual(source.read_bytes(), b"selected source")


    def test_cli_records_terminal_render_failure_in_reserved_report(self):
        report_path = self.root / "failed-report.json"
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
            "--execute", "--confirm-rights",
        ]):
            with patch(
                "backend.app.single_clip_render.render_selected_clip",
                side_effect=RuntimeError("simulated render failure"),
            ):
                self.assertEqual(main(), 1)

        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(report["execution_requested"])
        self.assertEqual(report["error"], "simulated render failure")
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        self.assertIn("inspect any output file", report["message"])
        self.assertFalse(self.output.exists())


    def test_candidate_csv_accepts_utf8_bom_from_spreadsheet_export(self):
        pack = self.root / "bom-candidates.csv"
        pack.write_text(
            "\ufeffsource_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,2,8,6,True\n",
            encoding="utf-8",
        )
        selected = load_selected_candidate(pack, 1)
        self.assertEqual(selected["source_id"], "authorized-demo")

    def test_candidate_csv_rejects_duplicate_required_headers(self):
        pack = self.root / "duplicate-headers.csv"
        pack.write_text(
            "source_id,source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "one,two,2,8,6,True\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "duplicate column names"):
            load_selected_candidate(pack, 1)

    def test_candidate_csv_rejects_selected_row_with_extra_values(self):
        pack = self.root / "extra-values.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,2,8,6,True,unexpected\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "more values than its header"):
            load_selected_candidate(pack, 1)

    def test_candidate_csv_rejects_selected_row_missing_required_value(self):
        pack = self.root / "missing-value.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,2,8,,True\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "missing required values"):
            load_selected_candidate(pack, 1)


if __name__ == "__main__":
    unittest.main()
