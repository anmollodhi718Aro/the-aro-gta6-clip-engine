"""Tests for the one-selected-video clip render path."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.single_clip_render import main, render_selected_clip


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

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_dry_run_plans_exactly_one_clip_without_rendering(self, preflight):
        with patch("backend.app.single_clip_render.render_clip") as render:
            report = render_selected_clip(self.source, self.output, 2, 8)
        self.assertEqual(report["status"], "PLANNED")
        self.assertFalse(report["processing_started"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        render.assert_not_called()
        preflight.assert_called_once_with(self.source, ffprobe_binary="ffprobe")

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_execution_requires_explicit_rights_confirmation(self, _preflight):
        report = render_selected_clip(self.source, self.output, 2, 8, execute=True)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["processing_started"])

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
    def test_rejects_output_that_fails_post_render_verification(self, render, preflight):
        render.return_value = self.output.resolve()
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
    def test_cli_writes_exclusive_dry_run_report(self, _preflight):
        report_path = self.root / "report.json"
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]):
            self.assertEqual(main(), 0)
        self.assertTrue(report_path.is_file())
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]):
            self.assertEqual(main(), 2)


if __name__ == "__main__":
    unittest.main()
