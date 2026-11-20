"""Tests for the offline clip review dashboard."""
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from unittest.mock import patch
from pathlib import Path

from backend.app.review_dashboard import load_report, main, render_dashboard


class ReviewDashboardTests(unittest.TestCase):
    def test_loads_report_and_renders_candidate_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / "report.json"
            report.write_text(json.dumps([
                {"candidate_row": 1, "source_id": "creator-1", "start_seconds": 12.5,
                 "end_seconds": 30.0, "status": "rendered", "message": "ready for review"},
                {"candidate_row": 2, "source_id": "creator-2", "status": "failed", "message": "encoder error"},
            ]), encoding="utf-8")
            rows = load_report(report)
        page = render_dashboard(rows)
        self.assertIn("creator-1", page)
        self.assertIn("encoder error", page)
        self.assertIn("Rendered", page)
        self.assertIn("failed", page)
        self.assertIn("12.5", page)
        self.assertIn("Export selected review rows", page)
        self.assertIn("aro_review_selection.json", page)
        self.assertIn("publish_approved:false", page)
        self.assertIn("review_selected:true", page)

    def test_escapes_untrusted_report_content(self):
        page = render_dashboard([{
            "candidate_row": 1, "source_id": "<script>alert(1)</script>",
            "status": "planned", "message": "<img src=x onerror=alert(1)>",
        }])
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertNotIn("<img src=x onerror=alert(1)>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_rejects_unknown_status(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / "report.json"
            report.write_text('[{"status":"published"}]', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unknown status"):
                load_report(report)

    def test_rejects_non_list_report(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / "report.json"
            report.write_text('{"status":"rendered"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "JSON list"):
                load_report(report)

    def test_empty_report_shows_empty_state(self):
        self.assertIn("No candidates in this report.", render_dashboard([]))


    def test_cli_refuses_to_overwrite_existing_dashboard(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "report.json"
            output = root / "dashboard.html"
            report.write_text('[{"status":"rendered"}]', encoding="utf-8")
            output.write_text("keep existing dashboard", encoding="utf-8")
            stderr = StringIO()
            with patch("sys.argv", ["review_dashboard", str(report), "--output", str(output)]):
                with redirect_stderr(stderr):
                    result = main()
            self.assertEqual(result, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep existing dashboard")
            self.assertIn("already exists", stderr.getvalue())

    def test_cli_creates_dashboard_when_output_is_new(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "report.json"
            output = root / "nested" / "dashboard.html"
            report.write_text('[{"status":"rendered"}]', encoding="utf-8")
            with patch("sys.argv", ["review_dashboard", str(report), "--output", str(output)]):
                result = main()
            self.assertEqual(result, 0)
            self.assertIn("Clip Review Dashboard", output.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
