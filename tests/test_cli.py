"""CLI integration tests using synthetic event data."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_cli_refuses_output_path_that_is_the_input_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            input_path = self.write_input(folder, ["analyze_chat"])
            original = input_path.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()):
                status = analyze_file(input_path, input_path, DetectorConfig())
            self.assertEqual(status, 2)
            self.assertEqual(input_path.read_bytes(), original)

    def test_cli_refuses_output_path_alias_of_input_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            input_path = self.write_input(folder, ["analyze_chat"])
            alias_path = Path(folder) / "." / "input.json"
            original = input_path.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()):
                status = analyze_file(input_path, alias_path, DetectorConfig())
            self.assertEqual(status, 2)
            self.assertEqual(input_path.read_bytes(), original)

    def test_cli_refuses_symbolic_link_output_without_replacing_target(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            input_path = self.write_input(folder, ["analyze_chat"])
            target_path = Path(folder) / "target.json"
            output_path = Path(folder) / "output.json"
            original = '{"keep": "target contents"}'
            target_path.write_text(original, encoding="utf-8")
            try:
                output_path.symlink_to(target_path)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable on this runner")

            with contextlib.redirect_stderr(io.StringIO()):
                status = analyze_file(input_path, output_path, DetectorConfig())

            self.assertEqual(status, 2)
            self.assertEqual(target_path.read_text(encoding="utf-8"), original)
            self.assertTrue(output_path.is_symlink())

    def test_cli_does_not_follow_output_symlink_created_after_initial_check(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            input_path = self.write_input(folder, ["analyze_chat"])
            target_path = Path(folder) / "target.json"
            output_path = Path(folder) / "output.json"
            original = '{"keep": "target contents"}'
            target_path.write_text(original, encoding="utf-8")
            original_resolve = Path.resolve

            def create_symlink_during_resolution(path, *args, **kwargs):
                if path == output_path and not output_path.exists() and not output_path.is_symlink():
                    try:
                        output_path.symlink_to(target_path)
                    except (OSError, NotImplementedError):
                        self.skipTest("symlink creation is unavailable on this runner")
                return original_resolve(path, *args, **kwargs)

            with patch.object(Path, "resolve", new=create_symlink_during_resolution):
                with contextlib.redirect_stdout(io.StringIO()):
                    status = analyze_file(input_path, output_path, DetectorConfig())

            self.assertEqual(status, 0)
            self.assertEqual(target_path.read_text(encoding="utf-8"), original)
            self.assertFalse(output_path.is_symlink())
            result = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(result["publishing_enabled"])


    def test_cli_rejects_non_object_top_level_json(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            input_path = Path(folder) / "input.json"
            output_path = Path(folder) / "output.json"
            input_path.write_text("[]", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                status = analyze_file(input_path, output_path, DetectorConfig())
            self.assertEqual(status, 2)
            self.assertFalse(output_path.exists())

    def test_cli_rejects_non_list_events(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            input_path = self.write_input(folder, ["analyze_chat"])
            payload = json.loads(input_path.read_text(encoding="utf-8"))
            payload["events"] = {"not": "a list"}
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            output_path = Path(folder) / "output.json"
            with contextlib.redirect_stderr(io.StringIO()):
                status = analyze_file(input_path, output_path, DetectorConfig())
            self.assertEqual(status, 2)
            self.assertFalse(output_path.exists())

    def test_failed_atomic_replace_preserves_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            input_path = self.write_input(folder, ["analyze_chat"])
            output_path = Path(folder) / "output.json"
            original = '{"previous": "complete"}'
            output_path.write_text(original, encoding="utf-8")

            with patch("backend.app.cli.os.replace", side_effect=OSError("simulated replace failure")):
                with contextlib.redirect_stderr(io.StringIO()):
                    status = analyze_file(input_path, output_path, DetectorConfig())

            self.assertEqual(status, 2)
            self.assertEqual(output_path.read_text(encoding="utf-8"), original)
            self.assertEqual(list(Path(folder).glob(".output.json.*.tmp")), [])


    def test_cli_reports_path_resolution_runtime_error_without_writing_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            input_path = self.write_input(folder, ["analyze_chat"])
            output_path = Path(folder) / "output.json"
            with patch.object(Path, "resolve", side_effect=RuntimeError("simulated symlink loop")):
                with contextlib.redirect_stderr(io.StringIO()) as stderr:
                    status = analyze_file(input_path, output_path, DetectorConfig())

            self.assertEqual(status, 2)
            self.assertIn("simulated symlink loop", stderr.getvalue())
            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
