import json
import tempfile
import unittest
from pathlib import Path

from backend.app.creator_watchlist_dashboard import load_ranking_report, render_dashboard, run


class CreatorWatchlistDashboardTests(unittest.TestCase):
    def test_renders_offline_dashboard_and_escapes_untrusted_fields(self):
        report = {
            "period_days": 7,
            "rankings": [{
                "rank": 1,
                "creator": '<script>alert("x")</script>',
                "region": "India & Global",
                "views_7d": 1234,
                "live_streams_7d": 2,
                "peak_concurrent_viewers": 50,
                "source_url": "https://www.youtube.com/watch?v=example",
            }],
        }
        page = render_dashboard(report)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>", page)
        self.assertIn("1,234", page)
        self.assertIn('rel="noopener noreferrer"', page)
        self.assertIn("default-src 'none'", page)
        self.assertNotIn("https://", page.split("<style>", 1)[0].replace(
            "https://www.youtube.com/watch?v=example", ""
        ))

    def test_rejects_non_https_evidence_link(self):
        page = render_dashboard({
            "rankings": [{
                "rank": 1, "creator": "Creator", "views_7d": 1,
                "live_streams_7d": 0, "source_url": "javascript:alert(1)"
            }]
        })
        self.assertNotIn('href="javascript:', page)
        self.assertIn("Not supplied", page)

    def test_rejects_malformed_report_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            path.write_text(json.dumps({"rankings": ["not-an-object"]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be an object"):
                load_ranking_report(path)

    def test_rejects_negative_counts(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            path.write_text(json.dumps({"rankings": [{
                "rank": 1, "creator": "Creator", "views_7d": -1,
                "live_streams_7d": 0
            }]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-negative"):
                load_ranking_report(path)

    def test_cli_writes_dashboard(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "report.json"
            output = root / "dashboard.html"
            source.write_text(json.dumps({"period_days": 7, "rankings": []}), encoding="utf-8")
            self.assertEqual(run(source, output), 0)
            self.assertIn("THE ARO Creator Watchlist", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
