import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app import quick_clip


class QuickClipCliTests(unittest.TestCase):
    def test_requires_explicit_rights_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "gameplay.mp4"
            source.touch()
            result = quick_clip.main([
                str(source), "--start", "10", "--end", "25",
                "--output", str(Path(directory) / "clip.mp4"),
            ])
            self.assertEqual(result, 2)

    def test_calls_local_renderer_and_reports_manual_review(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "gameplay.mp4"
            output = Path(directory) / "clip.mp4"
            source.touch()
            with patch("backend.app.quick_clip.render_clip", return_value=output) as render:
                result = quick_clip.main([
                    str(source), "--start", "10", "--end", "25",
                    "--output", str(output), "--confirm-rights",
                ])
            self.assertEqual(result, 0)
            self.assertTrue(render.called)
            self.assertTrue(render.call_args.kwargs["rights_confirmed"])
            self.assertEqual(render.call_args.kwargs["ffmpeg_binary"], "ffmpeg")

    def test_rejects_invalid_bounds_without_calling_renderer(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "gameplay.mp4"
            source.touch()
            with patch("backend.app.quick_clip.render_clip") as render:
                result = quick_clip.main([
                    str(source), "--start", "30", "--end", "10",
                    "--output", str(Path(directory) / "clip.mp4"),
                    "--confirm-rights",
                ])
            self.assertEqual(result, 2)
            render.assert_called_once()

    def test_success_report_explicitly_does_not_approve_upload(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "gameplay.mp4"
            output = Path(directory) / "clip.mp4"
            source.touch()
            with patch("backend.app.quick_clip.render_clip", return_value=output):
                with patch("builtins.print") as printed:
                    result = quick_clip.main([
                        str(source), "--start", "3", "--end", "18",
                        "--output", str(output), "--confirm-rights",
                    ])
            self.assertEqual(result, 0)
            payload = json.loads(printed.call_args.args[0])
            self.assertEqual(payload["duration_seconds"], 15)
            self.assertFalse(payload["upload_approved"])
            self.assertTrue(payload["manual_review_required"])


if __name__ == "__main__":
    unittest.main()
