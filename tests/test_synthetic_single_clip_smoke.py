"""Tests for the generated-media single-clip smoke-test harness."""
import ast
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import synthetic_single_clip_smoke as smoke


class SyntheticSingleClipSmokeTests(unittest.TestCase):
    def test_test_method_names_are_unique_for_unittest_discovery(self):
        source = Path(__file__).read_text(encoding="utf-8")
        module = ast.parse(source)
        test_classes = [
            node for node in module.body
            if isinstance(node, ast.ClassDef) and node.name == "SyntheticSingleClipSmokeTests"
        ]
        self.assertEqual(len(test_classes), 1)
        method_names = [
            node.name for node in test_classes[0].body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        ]
        self.assertEqual(len(method_names), len(set(method_names)), "duplicate test method names are silently overwritten")

    def test_final_lstat_cleanup_regression_is_a_direct_discoverable_method(self):
        source = Path(__file__).read_text(encoding="utf-8")
        module = ast.parse(source)
        test_classes = [
            node for node in module.body
            if isinstance(node, ast.ClassDef) and node.name == "SyntheticSingleClipSmokeTests"
        ]
        self.assertEqual(len(test_classes), 1)
        method_names = [
            node.name for node in test_classes[0].body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        self.assertEqual(
            method_names.count("test_hash_verified_output_closes_descriptor_when_final_lstat_fails"),
            1,
            "final-lstat cleanup regression must be defined directly on the test class",
        )

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


    def test_main_emits_structured_failure_for_non_json_renderer_report(self):
        import contextlib
        import io
        import json
        import sys

        stderr = io.StringIO()
        malformed_report = {"status": "FAILED", "unserializable": object()}
        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ), patch.object(smoke, "render_selected_clip", return_value=malformed_report), patch.object(
            sys, "argv", ["synthetic_single_clip_smoke.py"]
        ), contextlib.redirect_stderr(stderr):
            exit_code = smoke.main()

        self.assertEqual(exit_code, 1)
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("not valid JSON", payload["error"])
        self.assertFalse(payload["upload_performed"])
        self.assertFalse(payload["publishing_enabled"])

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


    def test_hash_verified_output_rejects_empty_file(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "empty.mp4"
            output.write_bytes(b"")
            with self.assertRaisesRegex(RuntimeError, "synthetic output is empty"):
                smoke._hash_verified_output(output)


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

    def test_hash_verified_output_rejects_path_swap_between_lstat_and_open(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "output.mp4"
            preserved = root / "original.mp4"
            target = root / "replacement.mp4"
            output.write_bytes(b"original synthetic output")
            target.write_bytes(b"replacement synthetic output")
            real_open = smoke.os.open
            swapped = {"done": False}

            def replace_before_open(path, flags, *args, **kwargs):
                if Path(path) == output and not swapped["done"]:
                    output.replace(preserved)
                    try:
                        output.symlink_to(target)
                    except (OSError, NotImplementedError) as exc:
                        preserved.replace(output)
                        raise unittest.SkipTest(
                            f"symlink creation unavailable for race regression: {exc}"
                        )
                    swapped["done"] = True
                return real_open(path, flags, *args, **kwargs)

            with patch.object(smoke.os, "open", side_effect=replace_before_open):
                with self.assertRaises((OSError, RuntimeError)):
                    smoke._hash_verified_output(output)

            self.assertTrue(swapped["done"])
            self.assertEqual(preserved.read_bytes(), b"original synthetic output")
            self.assertTrue(output.is_symlink())


    def test_renderer_exception_removes_temporary_directory(self):
        captured = {}

        def failing_render(source, output, start, end, **kwargs):
            captured["source"] = Path(source)
            captured["output"] = Path(output)
            captured["directory"] = Path(output).parent
            captured["output"].write_bytes(b"partial synthetic output")
            raise OSError("simulated renderer I/O failure")

        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ), patch.object(smoke, "render_selected_clip", side_effect=failing_render):
            with self.assertRaisesRegex(OSError, "simulated renderer I/O failure"):
                smoke.run_smoke_test()

        self.assertFalse(captured["source"].exists())
        self.assertFalse(captured["output"].exists())
        self.assertFalse(captured["directory"].exists())


    def test_non_rendered_report_removes_temporary_directory(self):
        captured = {}

        def failed_report(source, output, start, end, **kwargs):
            captured["source"] = Path(source)
            captured["output"] = Path(output)
            captured["directory"] = Path(output).parent
            return {
                "status": "FAILED",
                "upload_performed": False,
                "publishing_enabled": False,
            }

        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ), patch.object(smoke, "render_selected_clip", side_effect=failed_report):
            with self.assertRaisesRegex(RuntimeError, "did not return RENDERED"):
                smoke.run_smoke_test()

        self.assertFalse(captured["source"].exists())
        self.assertFalse(captured["output"].exists())
        self.assertFalse(captured["directory"].exists())

    def test_hash_verified_output_rejects_path_replacement_after_open(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "output.mp4"
            preserved = root / "original.mp4"
            replacement = root / "replacement.mp4"
            output.write_bytes(b"A" * (2 * 1024 * 1024))
            replacement.write_bytes(b"replacement bytes")
            real_read = smoke.os.read
            swapped = {"done": False}

            def replace_after_open(descriptor, size):
                chunk = real_read(descriptor, min(size, 1024 * 1024))
                if chunk and not swapped["done"]:
                    output.replace(preserved)
                    try:
                        output.symlink_to(replacement)
                    except (OSError, NotImplementedError) as exc:
                        preserved.replace(output)
                        raise unittest.SkipTest(
                            f"symlink creation unavailable for post-open race regression: {exc}"
                        )
                    swapped["done"] = True
                return chunk

            with patch.object(smoke.os, "read", side_effect=replace_after_open):
                with self.assertRaisesRegex(RuntimeError, "changed during SHA-256 verification"):
                    smoke._hash_verified_output(output)

            self.assertTrue(swapped["done"])
            self.assertEqual(preserved.stat().st_size, 2 * 1024 * 1024)
            self.assertEqual(replacement.read_bytes(), b"replacement bytes")
            self.assertTrue(output.is_symlink())


    def test_fixture_generation_timeout_prevents_render_and_cleans_temporary_directory(self):
        import subprocess
        captured = {}

        def timed_out(command, **kwargs):
            captured["directory"] = Path(command[-1]).parent
            captured["source"] = Path(command[-1])
            captured["timeout"] = kwargs.get("timeout")
            raise subprocess.TimeoutExpired(command, kwargs.get("timeout"))

        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run", side_effect=timed_out
        ), patch.object(smoke, "render_selected_clip") as render:
            with self.assertRaises(subprocess.TimeoutExpired):
                smoke.run_smoke_test()

        self.assertEqual(captured["timeout"], 120)
        render.assert_not_called()
        self.assertFalse(captured["source"].exists())
        self.assertFalse(captured["directory"].exists())


    def test_hash_verified_output_closes_descriptor_when_read_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output.mp4"
            output.write_bytes(b"synthetic output")
            opened = {}

            def fail_read(descriptor, size):
                opened["descriptor"] = descriptor
                raise OSError("simulated read failure")

            with patch.object(smoke.os, "read", side_effect=fail_read):
                with self.assertRaisesRegex(OSError, "simulated read failure"):
                    smoke._hash_verified_output(output)

            self.assertIn("descriptor", opened)
            with self.assertRaises(OSError):
                smoke.os.fstat(opened["descriptor"])



    def test_hash_verified_output_closes_descriptor_when_initial_fstat_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output.mp4"
            output.write_bytes(b"synthetic output")
            opened = {}
            real_fstat = smoke.os.fstat

            def fail_fstat(descriptor):
                opened["descriptor"] = descriptor
                raise OSError("simulated initial fstat failure")

            with patch.object(smoke.os, "fstat", side_effect=fail_fstat):
                with self.assertRaisesRegex(OSError, "simulated initial fstat failure"):
                    smoke._hash_verified_output(output)

            self.assertIn("descriptor", opened)
            with self.assertRaises(OSError):
                real_fstat(opened["descriptor"])


    def test_hash_verified_output_rejects_unexpected_early_eof_and_closes_descriptor(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output.mp4"
            output.write_bytes(b"complete synthetic output")
            opened = {}

            def return_early_eof(descriptor, size):
                opened["descriptor"] = descriptor
                return b""

            with patch.object(smoke.os, "read", side_effect=return_early_eof):
                with self.assertRaisesRegex(
                    RuntimeError, "changed during SHA-256 verification"
                ):
                    smoke._hash_verified_output(output)

            self.assertIn("descriptor", opened)
            with self.assertRaises(OSError):
                smoke.os.fstat(opened["descriptor"])


    def test_hash_verified_output_closes_descriptor_when_final_lstat_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output.mp4"
            output.write_bytes(b"synthetic output")
            real_open = smoke.os.open
            real_fstat = smoke.os.fstat
            real_lstat = Path.lstat
            opened = {}
            lstat_calls = {"count": 0}

            def capture_open(path, flags, *args, **kwargs):
                descriptor = real_open(path, flags, *args, **kwargs)
                opened["descriptor"] = descriptor
                return descriptor

            def fail_final_lstat(path, *args, **kwargs):
                if path == output:
                    lstat_calls["count"] += 1
                    if lstat_calls["count"] == 2:
                        raise OSError("simulated final pathname inspection failure")
                return real_lstat(path, *args, **kwargs)

            with patch.object(smoke.os, "open", side_effect=capture_open), patch.object(
                Path, "lstat", fail_final_lstat
            ):
                with self.assertRaisesRegex(OSError, "simulated final pathname inspection failure"):
                    smoke._hash_verified_output(output)

            self.assertEqual(lstat_calls["count"], 2)
            self.assertIn("descriptor", opened)
            with self.assertRaises(OSError):
                real_fstat(opened["descriptor"])


    def test_hash_verified_output_closes_descriptor_when_final_fstat_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output.mp4"
            output.write_bytes(b"verified synthetic output")
            real_open = smoke.os.open
            real_fstat = smoke.os.fstat
            opened = []
            calls = {"count": 0}

            def capture_open(path, flags, *args, **kwargs):
                descriptor = real_open(path, flags, *args, **kwargs)
                opened.append(descriptor)
                return descriptor

            def fail_final_fstat(descriptor):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("simulated final descriptor stat failure")
                return real_fstat(descriptor)

            with patch.object(smoke.os, "open", side_effect=capture_open), patch.object(
                smoke.os, "fstat", side_effect=fail_final_fstat
            ):
                with self.assertRaisesRegex(OSError, "final descriptor stat failure"):
                    smoke._hash_verified_output(output)

            self.assertEqual(calls["count"], 2)
            self.assertEqual(len(opened), 1)
            with self.assertRaises(OSError):
                real_fstat(opened[0])



    def test_smoke_harness_rejects_empty_rendered_output_even_with_matching_digest(self):
        def fake_render(source, output, start, end, **kwargs):
            Path(output).write_bytes(b"")
            return {
                "status": "RENDERED",
                "output_sha256": hashlib.sha256(b"").hexdigest(),
                "upload_performed": False,
                "publishing_enabled": False,
            }

        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ), patch.object(smoke, "render_selected_clip", side_effect=fake_render):
            with self.assertRaisesRegex(RuntimeError, "synthetic output is empty"):
                smoke.run_smoke_test()


    def test_main_emits_structured_failure_for_overflow(self):
        import contextlib
        import io
        import json
        import sys

        stderr = io.StringIO()
        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ), patch.object(smoke, "render_selected_clip", side_effect=OverflowError("duration conversion overflow")), patch.object(
            sys, "argv", ["synthetic_single_clip_smoke.py"]
        ), contextlib.redirect_stderr(stderr):
            exit_code = smoke.main()

        self.assertEqual(exit_code, 1)
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("OverflowError", payload["error"])
        self.assertIn("duration conversion overflow", payload["error"])
        self.assertFalse(payload["upload_performed"])
        self.assertFalse(payload["publishing_enabled"])


    def test_main_emits_structured_failure_for_empty_synthetic_output(self):
        import contextlib
        import io
        import json
        import sys

        def fake_render(source, output, start, end, **kwargs):
            Path(output).write_bytes(b"")
            return {
                "status": "RENDERED",
                "output_sha256": hashlib.sha256(b"").hexdigest(),
                "upload_performed": False,
                "publishing_enabled": False,
            }

        stderr = io.StringIO()
        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ), patch.object(smoke, "render_selected_clip", side_effect=fake_render), patch.object(
            sys, "argv", ["synthetic_single_clip_smoke.py"]
        ), contextlib.redirect_stderr(stderr):
            exit_code = smoke.main()

        self.assertEqual(exit_code, 1)
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("synthetic output is empty", payload["error"])
        self.assertFalse(payload["upload_performed"])
        self.assertFalse(payload["publishing_enabled"])


    def test_main_emits_structured_success_for_valid_synthetic_output(self):
        import contextlib
        import io
        import json
        import sys

        def fake_render(source, output, start, end, **kwargs):
            payload = b"valid synthetic rendered mp4"
            Path(output).write_bytes(payload)
            return {
                "status": "RENDERED",
                "output_sha256": hashlib.sha256(payload).hexdigest(),
                "upload_performed": False,
                "publishing_enabled": False,
            }

        stdout = io.StringIO()
        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ), patch.object(smoke, "render_selected_clip", side_effect=fake_render), patch.object(
            sys, "argv", ["synthetic_single_clip_smoke.py"]
        ), contextlib.redirect_stdout(stdout):
            exit_code = smoke.main()

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["media"], "synthetic test pattern and tone only")
        self.assertEqual(payload["selected_clip_seconds"], 4)
        self.assertGreater(payload["output_size_bytes"], 0)
        self.assertEqual(payload["output_sha256"], hashlib.sha256(b"valid synthetic rendered mp4").hexdigest())
        self.assertFalse(payload["upload_performed"])
        self.assertFalse(payload["publishing_enabled"])
        self.assertTrue(payload["manual_review_required"])
        self.assertFalse(payload["artifacts_retained"])


    def test_main_emits_structured_failure_when_renderer_reports_missing_output(self):
        import contextlib
        import io
        import json
        import sys

        def fake_render(source, output, start, end, **kwargs):
            # Deliberately claim success without creating the requested artifact.
            return {
                "status": "RENDERED",
                "output_sha256": hashlib.sha256(b"plausible but absent output").hexdigest(),
                "upload_performed": False,
                "publishing_enabled": False,
            }

        stderr = io.StringIO()
        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run"
        ), patch.object(smoke, "render_selected_clip", side_effect=fake_render), patch.object(
            sys, "argv", ["synthetic_single_clip_smoke.py"]
        ), contextlib.redirect_stderr(stderr):
            exit_code = smoke.main()

        self.assertEqual(exit_code, 1)
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("synthetic output is missing", payload["error"])
        self.assertFalse(payload["upload_performed"])
        self.assertFalse(payload["publishing_enabled"])



    def test_main_emits_structured_failure_and_cleans_up_when_fixture_generation_times_out(self):
        import contextlib
        import io
        import json
        import subprocess
        import sys

        captured = {}
        stderr = io.StringIO()

        def timeout_fixture_generation(command, **kwargs):
            captured["temporary_directory"] = Path(command[-1]).parent
            captured["timeout"] = kwargs.get("timeout")
            raise subprocess.TimeoutExpired(command, kwargs.get("timeout"))

        with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
            smoke.subprocess, "run", side_effect=timeout_fixture_generation
        ), patch.object(smoke, "render_selected_clip") as render, patch.object(
            sys, "argv", ["synthetic_single_clip_smoke.py"]
        ), contextlib.redirect_stderr(stderr):
            exit_code = smoke.main()

        self.assertEqual(exit_code, 1)
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("TimeoutExpired", payload["error"])
        self.assertIn("120", payload["error"])
        self.assertFalse(payload["upload_performed"])
        self.assertFalse(payload["publishing_enabled"])
        self.assertEqual(captured["timeout"], 120)
        render.assert_not_called()
        self.assertFalse(captured["temporary_directory"].exists())



    def test_smoke_harness_rejects_renderer_report_that_enables_upload_or_publishing(self):
        for unsafe_flag in ("upload_performed", "publishing_enabled"):
            with self.subTest(unsafe_flag=unsafe_flag):
                captured = {}

                def unsafe_render(source, output, start, end, **kwargs):
                    captured["source"] = Path(source)
                    captured["output"] = Path(output)
                    captured["directory"] = Path(output).parent
                    payload = b"synthetic rendered output"
                    captured["output"].write_bytes(payload)
                    return {
                        "status": "RENDERED",
                        "output_sha256": hashlib.sha256(payload).hexdigest(),
                        "upload_performed": unsafe_flag == "upload_performed",
                        "publishing_enabled": unsafe_flag == "publishing_enabled",
                    }

                with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
                    smoke.subprocess, "run"
                ), patch.object(smoke, "render_selected_clip", side_effect=unsafe_render):
                    with self.assertRaisesRegex(
                        RuntimeError, "unexpectedly enabled upload or publishing"
                    ):
                        smoke.run_smoke_test()

                self.assertFalse(captured["source"].exists())
                self.assertFalse(captured["output"].exists())
                self.assertFalse(captured["directory"].exists())

    @unittest.skipUnless(
        hasattr(smoke.os, "mkfifo") and hasattr(smoke.os, "O_NONBLOCK"),
        "FIFO replacement race requires POSIX mkfifo and O_NONBLOCK",
    )
    def test_hash_verified_output_rejects_fifo_replacement_without_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output.mp4"
            output.write_bytes(b"initial regular output")
            real_open = smoke.os.open
            observed = {}

            def replace_with_fifo(path, flags, *args, **kwargs):
                output.unlink()
                smoke.os.mkfifo(output)
                observed["flags"] = flags
                return real_open(path, flags, *args, **kwargs)

            with patch.object(smoke.os, "open", side_effect=replace_with_fifo):
                with self.assertRaisesRegex(
                    RuntimeError, "changed while opening it for verification"
                ):
                    smoke._hash_verified_output(output)

            self.assertIn("flags", observed)
            self.assertTrue(observed["flags"] & smoke.os.O_NONBLOCK)
            self.assertTrue(output.exists())
            self.assertTrue(smoke.stat.S_ISFIFO(output.lstat().st_mode))



if __name__ == "__main__":
    unittest.main()
