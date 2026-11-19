"""Tests for the offline clip review dashboard."""
import json
import tempfile
import unittest
from pathlib import Path

from backend.app.review_dashboard import load_report, render_dashboard


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


if __name__ == "__main__":
    unittest.main()
