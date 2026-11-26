"""Tests for the generated-media single-clip smoke-test harness."""
import hashlib
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import synthetic_single_clip_smoke as smoke


class SyntheticSingleClipSmokeTests(unittest.TestCase):
    def test_missing_ffmpeg_is_reported_as_a_normal_error(self):
        with patch.object(smoke.shutil, "which", return_value=None):
            with self.assertRaisesRegex(FileNotFoundError, "ffmpeg"):
                smoke._require_executable("ffmpeg")

    def test_missing_ffprobe_is_reported_before_fixture_generation(self):
        with patch.object(smoke.shutil, "which", side_effect=lambda name: None if name == "ffprobe" else "/tools/ffmpeg"), patch.object(
            smoke.subprocess, "run"
        ) as generate:
            with self.assertRaisesRegex(FileNotFoundError, "ffprobe"):
                smoke.run_smoke_test()
        generate.assert_not_called()

    def test_main_emits_structured_failure_when_ffmpeg_is_missing(self):
        import contextlib
        import io
        import json
        import sys

        stderr = io.StringIO()
        with patch.object(smoke.shutil, "which", return_value=None), patch.object(
            sys, "argv", ["synthetic_single_clip_smoke.py"]
        ), contextlib.redirect_stderr(stderr):
            exit_code = smoke.main()

        self.assertEqual(exit_code, 1)
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("ffmpeg", payload["error"])
        self.assertFalse(payload["upload_performed"])
        self.assertFalse(payload["publishing_enabled"])

    def test_ffmpeg_fixture_generation_failure_is_not_reported_as_pass(self):
        import subprocess

        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run", side_effect=subprocess.CalledProcessError(1, ["ffmpeg"])
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                smoke.run_smoke_test()

    def test_smoke_harness_checks_render_and_removes_temporary_artifacts(self):
        captured = {}

        def fake_render(source, output, start, end, **kwargs):
            captured["source"] = Path(source)
            captured["output"] = Path(output)
            captured["start"] = start
            captured["end"] = end
            captured["kwargs"] = kwargs
            Path(output).write_bytes(b"synthetic-rendered-mp4")
            return {
                "status": "RENDERED",
                "output_sha256": hashlib.sha256(Path(output).read_bytes()).hexdigest(),
                "upload_performed": False,
                "publishing_enabled": False,
            }

        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ) as generate, patch.object(smoke, "render_selected_clip", side_effect=fake_render):
            result = smoke.run_smoke_test()

        generate.assert_called_once()
        command = generate.call_args.args[0]
        self.assertIn("testsrc2=size=640x360:rate=30", command)
        self.assertIn("sine=frequency=440:sample_rate=48000", command)
        self.assertEqual(captured["start"], 1.0)
        self.assertEqual(captured["end"], 5.0)
        self.assertTrue(captured["kwargs"]["execute"])
        self.assertTrue(captured["kwargs"]["rights_confirmed"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["output_sha256"], hashlib.sha256(b"synthetic-rendered-mp4").hexdigest())
        self.assertFalse(result["upload_performed"])
        self.assertFalse(result["publishing_enabled"])
        self.assertFalse(captured["source"].exists())
        self.assertFalse(captured["output"].exists())

    def test_rejects_well_formed_digest_that_does_not_match_output_bytes(self):
        def fake_render(source, output, start, end, **kwargs):
            Path(output).write_bytes(b"synthetic-rendered-mp4")
            return {
                "status": "RENDERED",
                "output_sha256": hashlib.sha256(b"synthetic-rendered-mp4").hexdigest(),
                "upload_performed": False,
                "publishing_enabled": False,
            }

        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ), patch.object(smoke, "render_selected_clip", side_effect=fake_render):
            with self.assertRaisesRegex(RuntimeError, "does not match the rendered MP4 bytes"):
                smoke.run_smoke_test()

    def test_rejects_non_hex_output_digest(self):
        def fake_render(source, output, start, end, **kwargs):
            Path(output).write_bytes(b"synthetic-rendered-mp4")
            return {
                "status": "RENDERED",
                "output_sha256": "z" * 64,
                "upload_performed": False,
                "publishing_enabled": False,
            }

        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ), patch.object(smoke, "render_selected_clip", side_effect=fake_render):
            with self.assertRaisesRegex(RuntimeError, "valid output SHA-256"):
                smoke.run_smoke_test()


if __name__ == "__main__":
    unittest.main()
