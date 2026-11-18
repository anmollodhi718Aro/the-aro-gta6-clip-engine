"""CLI integration tests using synthetic event data."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from backend.app.cli import analyze_file
from backend.app.detection import DetectorConfig


class CliTests(unittest.TestCase):
    def write_input(self, folder: str, scopes: list[str]) -> Path:
        events = []
        for bucket in range(4):
            count = 9 if bucket == 3 else 2
            for item in range(count):
                second = bucket * 10 + item
                events.append({
                    "event_id": f"{bucket}-{item}",
                    "source_id": "demo",
                    "timestamp": f"2026-11-18T12:00:{second:02d}+00:00",
                    "text": "synthetic",
                })
        payload = {
            "permission": {
                "source_id": "demo",
                "granted_by": "test-fixture",
                "scopes": scopes,
                "granted_at": "2026-11-18T11:59:00+00:00",
                "expires_at": "2026-11-18T13:00:00+00:00",
            },
            "events": events,
        }
        path = Path(folder) / "input.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_cli_writes_review_only_clip_plan(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            input_path = self.write_input(folder, ["analyze_chat"])
            output_path = Path(folder) / "output.json"
            with contextlib.redirect_stdout(io.StringIO()):
                status = analyze_file(input_path, output_path, DetectorConfig())
            self.assertEqual(status, 0)
            result = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(result["candidate_count"], 1)
            self.assertEqual(result["candidates"][0]["status"], "needs_review")
            self.assertFalse(result["publishing_enabled"])

    def test_cli_stops_without_chat_permission(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            input_path = self.write_input(folder, ["view_only"])
            output_path = Path(folder) / "output.json"
            with contextlib.redirect_stderr(io.StringIO()):
                status = analyze_file(input_path, output_path, DetectorConfig())
            self.assertEqual(status, 2)
            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
