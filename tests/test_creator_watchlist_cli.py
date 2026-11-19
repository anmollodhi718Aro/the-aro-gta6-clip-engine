import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from backend.app.creator_watchlist_cli import run

START = datetime(2026, 11, 12, tzinfo=timezone.utc)
END = START + timedelta(days=7)


class CreatorWatchlistCliTests(unittest.TestCase):
    def _write_valid_input(self, source: Path) -> None:
        source.write_text(json.dumps({"metrics": [{
            "creator_id": "death-tracks-gaming",
            "window_start": START.isoformat(),
            "window_end": END.isoformat(),
            "views": 1500,
            "live_streams": 2,
            "peak_concurrent_viewers": 200,
            "average_concurrent_viewers": 100,
            "source_url": "https://www.youtube.com/watch?v=example"
        }]}), encoding="utf-8")

    def test_cli_writes_ranked_report(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "metrics.json"
            output = root / "out" / "ranking.json"
            self._write_valid_input(source)
            self.assertEqual(run(source, output), 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["rankings"][0]["creator"], "Death Tracks Gaming")
            self.assertEqual(report["rankings"][0]["rank"], 1)
            self.assertFalse(report["publishing_enabled"])

    def test_cli_rejects_timezone_without_offset(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "metrics.json"
            source.write_text(json.dumps({"metrics": [{
                "creator_id": "mythpat",
                "window_start": "2026-11-12T00:00:00",
                "window_end": END.isoformat(),
                "views": 10,
                "live_streams": 1,
                "source_url": "https://www.youtube.com/watch?v=example"
            }]}), encoding="utf-8")
            self.assertEqual(run(source, root / "out.json"), 2)

    def test_failed_atomic_replace_preserves_previous_report_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "metrics.json"
            output = root / "ranking.json"
            self._write_valid_input(source)
            output.write_text("previous complete report\n", encoding="utf-8")

            with patch(
                "backend.app.creator_watchlist_cli.os.replace",
                side_effect=OSError("simulated replace failure"),
            ):
                self.assertEqual(run(source, output), 2)

            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "previous complete report\n",
            )
            self.assertEqual(list(root.glob(".ranking.json.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
