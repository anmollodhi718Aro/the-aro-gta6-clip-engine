"""Tests for the generated-media single-clip smoke-test harness."""
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
                "output_sha256": "0" * 64,
                "upload_performed": False,
                "publishing_enabled": False,
            }

        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ), patch.object(smoke, "render_selected_clip", side_effect=fake_render):
            with self.assertRaisesRegex(RuntimeError, "does not match the rendered MP4 bytes"):
                smoke.run_smoke_test()

    def test_failure_removes_temporary_source_and_output_artifacts(self):
        captured = {}

        def fake_render(source, output, start, end, **kwargs):
            captured["source"] = Path(source)
            captured["output"] = Path(output)
            captured["directory"] = Path(output).parent
            captured["output"].write_bytes(b"synthetic-rendered-mp4")
            return {
                "status": "RENDERED",
                "output_sha256": "0" * 64,
                "upload_performed": False,
                "publishing_enabled": False,
            }

        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ), patch.object(smoke, "render_selected_clip", side_effect=fake_render):
            with self.assertRaisesRegex(RuntimeError, "does not match the rendered MP4 bytes"):
                smoke.run_smoke_test()

        self.assertFalse(captured["source"].exists())
        self.assertFalse(captured["output"].exists())
        self.assertFalse(captured["directory"].exists())

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


    def test_malformed_renderer_report_is_rejected(self):
        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ), patch.object(smoke, "render_selected_clip", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "malformed report"):
                smoke.run_smoke_test()


    def test_hash_verified_output_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target.mp4"
            link = root / "output.mp4"
            target.write_bytes(b"synthetic-output")
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaisesRegex(RuntimeError, "regular non-symlink"):
                smoke._hash_verified_output(link)

    def test_hash_verified_output_returns_digest_and_size_from_same_file(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output.mp4"
            payload = b"verified synthetic output"
            output.write_bytes(payload)
            digest, size = smoke._hash_verified_output(output)
            self.assertEqual(digest, hashlib.sha256(payload).hexdigest())
            self.assertEqual(size, len(payload))


    def test_hash_verified_output_rejects_in_place_mutation_during_read(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output.mp4"
            output.write_bytes(b"A" * (2 * 1024 * 1024))
            real_read = smoke.os.read
            calls = {"count": 0}

            def mutate_after_first_chunk(descriptor, size):
                chunk = real_read(descriptor, min(size, 1024 * 1024))
                calls["count"] += 1
                if calls["count"] == 1:
                    with output.open("r+b") as handle:
                        handle.seek(0)
                        handle.write(b"B" * 4096)
                        handle.flush()
                return chunk

            with patch.object(smoke.os, "read", side_effect=mutate_after_first_chunk):
                with self.assertRaisesRegex(RuntimeError, "changed during SHA-256 verification"):
                    smoke._hash_verified_output(output)

            self.assertGreaterEqual(calls["count"], 1)


if __name__ == "__main__":
    unittest.main()
