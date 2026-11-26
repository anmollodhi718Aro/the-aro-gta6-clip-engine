"""Regression tests for strict terminal-report serialization fallback."""
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from backend.app.single_clip_render import main


class TerminalSerializationFallbackTests(unittest.TestCase):
    def test_non_json_terminal_result_writes_strict_failure_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report_path = root / "render-report.json"
            output_path = root / "clip.mp4"
            fallback_path = report_path.with_name(
                report_path.name + ".terminal-fallback.json"
            )
            argv = [
                "single_clip_render.py",
                str(root / "selected.mp4"),
                "--start", "1",
                "--end", "5",
                "--output", str(output_path),
                "--report", str(report_path),
            ]
            stderr = StringIO()
            invalid_terminal_result = {
                "status": "RENDERED",
                "unexpected_value": object(),
                "upload_performed": False,
                "publishing_enabled": False,
            }
            with patch("sys.argv", argv), patch(
                "backend.app.single_clip_render.render_selected_clip",
                return_value=invalid_terminal_result,
            ), redirect_stderr(stderr):
                self.assertEqual(main(), 2)

            primary = json.loads(report_path.read_text(encoding="utf-8"))
            fallback_text = fallback_path.read_text(encoding="utf-8")
            fallback = json.loads(fallback_text)

            self.assertEqual(primary["status"], "RUNNING")
            self.assertEqual(fallback["status"], "FAIL")
            self.assertTrue(fallback["terminal_report_serialization_failed"])
            self.assertEqual(fallback["render_result_status"], "RENDERED")
            self.assertTrue(fallback["output_inspection_required"])
            self.assertFalse(fallback["upload_performed"])
            self.assertFalse(fallback["publishing_enabled"])
            self.assertTrue(fallback_text.endswith("\n"))
            self.assertIn("Inspect any output file manually before retrying", fallback["message"])
            self.assertIn(str(fallback_path), stderr.getvalue())
            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
