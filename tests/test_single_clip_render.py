"""Tests for the one-selected-video clip render path."""
import hashlib
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from backend.app.clip_pack import map_candidates_to_media, write_clip_pack
from backend.app.single_clip_render import (
    _create_stable_source_snapshot, _write_exclusive_terminal_fallback,
    load_selected_candidate, main, render_selected_clip, sha256_selected_source,
    _rendered_mp4_validation_error, _sha256_verified_regular_file,
    _fsync_parent_directory, _report_handle_matches_path,
)


PASS = {"status": "PASS", "duration_seconds": 20.0, "format_name": "mov,mp4,m4a,3gp,3g2,mj2", "video_streams": [{"codec": "h264", "width": 1080, "height": 1920}]}


class SingleClipRenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "selected.mp4"
        self.source.write_bytes(b"synthetic video")
        self.output = self.root / "clip.mp4"

    def tearDown(self):
        self.temp.cleanup()


    @unittest.skipIf(os.name == "nt", "portable Python cannot fsync directory handles on Windows")
    def test_fsync_parent_directory_syncs_the_containing_directory(self):
        target = self.root / "durable-report.json"
        real_open = os.open
        real_fsync = os.fsync
        opened = {}
        synced = []

        def recording_open(path, flags, *args, **kwargs):
            opened["path"] = Path(path)
            opened["flags"] = flags
            return real_open(path, flags, *args, **kwargs)

        def recording_fsync(descriptor):
            synced.append(descriptor)
            return real_fsync(descriptor)

        with patch("backend.app.single_clip_render.os.open", side_effect=recording_open), patch(
            "backend.app.single_clip_render.os.fsync", side_effect=recording_fsync
        ):
            _fsync_parent_directory(target)

        self.assertEqual(opened["path"], self.root)
        self.assertEqual(opened["flags"] & os.O_RDONLY, os.O_RDONLY)
        if hasattr(os, "O_DIRECTORY"):
            self.assertTrue(opened["flags"] & os.O_DIRECTORY)
        self.assertEqual(len(synced), 1)

    @unittest.skipUnless(os.name == "nt", "Windows-specific portability check")
    def test_fsync_parent_directory_is_noop_on_windows(self):
        with patch("backend.app.single_clip_render.os.open", side_effect=AssertionError("must not open directory")):
            _fsync_parent_directory(self.root / "durable-report.json")


    def test_verified_output_hash_rejects_path_replacement_after_open(self):
        replacement = self.root / "replacement.mp4"
        preserved = self.root / "preserved-original.mp4"
        replacement.write_bytes(b"replacement bytes")
        original_bytes = b"original rendered bytes"
        self.output.write_bytes(original_bytes)
        real_lstat = Path.lstat
        swapped = {"done": False}

        def replace_before_path_stat(path):
            if path == self.output and not swapped["done"]:
                self.output.replace(preserved)
                replacement.replace(self.output)
                swapped["done"] = True
            return real_lstat(path)

        with patch.object(Path, "lstat", new=replace_before_path_stat):
            with self.assertRaisesRegex(ValueError, "regular non-symlink file"):
                _sha256_verified_regular_file(self.output)

        self.assertTrue(swapped["done"])
        self.assertEqual(preserved.read_bytes(), original_bytes)
        self.assertEqual(self.output.read_bytes(), b"replacement bytes")


    def test_verified_output_hash_closes_descriptor_when_initial_path_stat_fails(self):
        real_open = os.open
        real_lstat = Path.lstat
        opened = {}

        def recording_open(path, flags, *args, **kwargs):
            descriptor = real_open(path, flags, *args, **kwargs)
            opened["descriptor"] = descriptor
            return descriptor

        def fail_selected_path_stat(path):
            if path == self.output:
                raise OSError("simulated initial path stat failure")
            return real_lstat(path)

        with patch("backend.app.single_clip_render.os.open", side_effect=recording_open), patch.object(
            Path, "lstat", new=fail_selected_path_stat
        ):
            with self.assertRaisesRegex(OSError, "simulated initial path stat failure"):
                _sha256_verified_regular_file(self.output)

        self.assertIn("descriptor", opened)
        with self.assertRaises(OSError):
            os.fstat(opened["descriptor"])


    def test_verified_output_hash_rejects_path_replacement_after_eof(self):
        replacement = self.root / "replacement-after-eof.mp4"
        preserved = self.root / "preserved-before-eof.mp4"
        original_bytes = b"original rendered bytes after final chunk"
        replacement_bytes = b"replacement bytes after EOF"
        self.output.write_bytes(original_bytes)
        replacement.write_bytes(replacement_bytes)
        real_read = os.read
        swapped = {"done": False}

        def replace_after_eof(descriptor, size):
            chunk = real_read(descriptor, size)
            if not chunk and not swapped["done"]:
                self.output.replace(preserved)
                replacement.replace(self.output)
                swapped["done"] = True
            return chunk

        with patch("backend.app.single_clip_render.os.read", side_effect=replace_after_eof):
            with self.assertRaisesRegex(RuntimeError, "changed during SHA-256 verification"):
                _sha256_verified_regular_file(self.output)

        self.assertTrue(swapped["done"])
        self.assertEqual(preserved.read_bytes(), original_bytes)
        self.assertEqual(self.output.read_bytes(), replacement_bytes)


    def test_render_selected_clip_reports_invalid_path_without_stringifying_unsafe_objects(self):
        class BrokenString:
            def __str__(self):
                raise RuntimeError("untrusted path string conversion failed")

        broken = BrokenString()
        invalid_video = render_selected_clip(broken, self.output, 1, 5)
        self.assertEqual(invalid_video["status"], "FAIL")
        self.assertEqual(invalid_video["source_path"], "<unavailable>")
        self.assertFalse(invalid_video["processing_started"])

        invalid_output = render_selected_clip(self.source, broken, 1, 5)
        self.assertEqual(invalid_output["status"], "FAIL")
        self.assertEqual(invalid_output["output_path"], "<unavailable>")
        self.assertFalse(invalid_output["processing_started"])

    def test_sha256_selected_source_rejects_invalid_path_arguments(self):
        for invalid_path in (None, 7, [], {}, "", "   ", "\t"):
            with self.subTest(invalid_path=repr(invalid_path)):
                with self.assertRaisesRegex(
                    ValueError,
                    "selected source path must be a non-empty string or pathlib.Path",
                ):
                    sha256_selected_source(invalid_path)

    def test_sha256_selected_source_matches_file_bytes(self):
        expected = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.assertEqual(sha256_selected_source(self.source), expected)

    def test_sha256_selected_source_uses_nonblocking_open_when_available(self):
        real_open = os.open
        observed = {}

        def recording_open(path, flags, *args, **kwargs):
            observed["flags"] = flags
            return real_open(path, flags, *args, **kwargs)

        with patch("backend.app.single_clip_render.os.open", side_effect=recording_open):
            sha256_selected_source(self.source)

        if hasattr(os, "O_NONBLOCK"):
            self.assertTrue(observed["flags"] & os.O_NONBLOCK)

    def test_sha256_selected_source_rejects_incomplete_read(self):
        with patch("backend.app.single_clip_render.os.read", return_value=b""):
            with self.assertRaisesRegex(ValueError, "changed while it was being hashed"):
                sha256_selected_source(self.source)


    def test_snapshot_cleanup_failure_is_reported_as_created_unverified(self):
        with patch(
            "backend.app.single_clip_render.os.read", return_value=b""
        ), patch.object(
            Path, "unlink", side_effect=PermissionError("simulated cleanup denial")
        ), patch(
            "backend.app.single_clip_render.render_clip"
        ) as render:
            report = render_selected_clip(
                self.source, self.output, 1, 5,
                execute=True, rights_confirmed=True,
            )

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(report["source_snapshot_created"])
        self.assertFalse(report["source_snapshot_verified"])
        self.assertTrue(report["source_snapshot_cleanup_required"])
        self.assertIsNone(report["source_sha256"])
        self.assertIn("partial source snapshot may remain", report["message"])
        render.assert_not_called()

    def test_source_ffprobe_exception_fails_closed_before_render(self):
        with patch(
            "backend.app.single_clip_render.inspect_one_video",
            side_effect=RuntimeError("simulated source ffprobe failure"),
        ), patch("backend.app.single_clip_render.render_clip") as render:
            report = render_selected_clip(
                self.source, self.output, 1, 5,
                execute=True, rights_confirmed=True,
            )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("RuntimeError: simulated source ffprobe failure", report["source_preflight_error"])
        self.assertTrue(report["source_inspection_required"])
        self.assertFalse(report["processing_started"])
        self.assertTrue(report["source_snapshot_created"])
        self.assertFalse(self.output.exists())
        self.assertIn("no render was started", report["message"])
        render.assert_not_called()

    def test_malformed_source_ffprobe_metadata_fails_closed_before_render(self):
        with patch(
            "backend.app.single_clip_render.inspect_one_video",
            return_value=["unexpected", "metadata"],
        ), patch("backend.app.single_clip_render.render_clip") as render:
            report = render_selected_clip(
                self.source, self.output, 1, 5,
                execute=True, rights_confirmed=True,
            )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("expected an object", report["source_preflight_error"])
        self.assertIn("list", report["source_preflight_error"])
        self.assertTrue(report["source_inspection_required"])
        self.assertFalse(report["processing_started"])
        self.assertTrue(report["source_snapshot_created"])
        self.assertFalse(self.output.exists())
        self.assertIn("no render was started", report["message"])
        render.assert_not_called()


    def test_snapshot_creation_checks_expected_digest_of_copied_bytes(self):
        expected = hashlib.sha256(self.source.read_bytes()).hexdigest()
        snapshot = self.root / "snapshot.mp4"
        actual = _create_stable_source_snapshot(
            self.source, snapshot, expected_sha256=expected
        )
        self.assertEqual(actual, expected)
        self.assertEqual(snapshot.read_bytes(), self.source.read_bytes())

    def test_snapshot_creation_fsyncs_parent_directory_after_file(self):
        snapshot = self.root / "directory-durable-snapshot.mp4"
        with patch(
            "backend.app.single_clip_render._fsync_parent_directory"
        ) as fsync_parent:
            _create_stable_source_snapshot(self.source, snapshot)

        fsync_parent.assert_called_once_with(snapshot)
        self.assertEqual(snapshot.read_bytes(), self.source.read_bytes())

    def test_snapshot_directory_fsync_failure_cleans_created_snapshot(self):
        snapshot = self.root / "directory-fsync-failure-snapshot.mp4"
        with patch(
            "backend.app.single_clip_render._fsync_parent_directory",
            side_effect=OSError("simulated directory fsync failure"),
        ):
            with self.assertRaisesRegex(OSError, "simulated directory fsync failure"):
                _create_stable_source_snapshot(self.source, snapshot)

        self.assertFalse(snapshot.exists())
        self.assertEqual(self.source.read_bytes(), b"synthetic video")

    def test_snapshot_directory_fsync_and_cleanup_failure_preserves_recovery_state(self):
        from backend.app.single_clip_render import SourceSnapshotCreationError

        snapshot = self.root / "directory-fsync-cleanup-failure-snapshot.mp4"
        with patch(
            "backend.app.single_clip_render._fsync_parent_directory",
            side_effect=OSError("simulated directory fsync failure"),
        ), patch.object(
            Path, "unlink", side_effect=PermissionError("simulated snapshot cleanup denial")
        ):
            with self.assertRaises(SourceSnapshotCreationError) as raised:
                _create_stable_source_snapshot(self.source, snapshot)

        self.assertTrue(raised.exception.snapshot_created)
        self.assertTrue(raised.exception.cleanup_required)
        self.assertIn("directory fsync failure", str(raised.exception))
        self.assertIn("cleanup could not be confirmed", str(raised.exception))
        self.assertTrue(snapshot.exists())
        self.assertEqual(snapshot.read_bytes(), self.source.read_bytes())
        self.assertEqual(self.source.read_bytes(), b"synthetic video")

    def test_snapshot_readback_uses_nonblocking_open_when_available(self):
        snapshot = self.root / "nonblocking-readback-snapshot.mp4"
        real_open = os.open
        observed = {}

        def recording_open(path, flags, *args, **kwargs):
            if Path(path) == snapshot:
                observed["flags"] = flags
            return real_open(path, flags, *args, **kwargs)

        with patch("backend.app.single_clip_render.os.open", side_effect=recording_open):
            _create_stable_source_snapshot(self.source, snapshot)

        if hasattr(os, "O_NONBLOCK"):
            self.assertIn("flags", observed)
            self.assertTrue(observed["flags"] & os.O_NONBLOCK)
        self.assertEqual(snapshot.read_bytes(), self.source.read_bytes())

    def test_snapshot_creation_rejects_readback_digest_mismatch_and_cleans_snapshot(self):
        snapshot = self.root / "readback-mismatch-snapshot.mp4"
        with patch(
            "backend.app.single_clip_render.os.read",
            side_effect=[b"tampered persisted bytes", b""],
        ):
            with self.assertRaisesRegex(OSError, "read-back SHA-256"):
                _create_stable_source_snapshot(self.source, snapshot)

        self.assertFalse(snapshot.exists())
        self.assertEqual(self.source.read_bytes(), b"synthetic video")

    def test_snapshot_readback_rejects_early_eof_and_cleans_snapshot(self):
        snapshot = self.root / "early-eof-readback-snapshot.mp4"
        with patch("backend.app.single_clip_render.os.read", return_value=b""):
            with self.assertRaisesRegex(RuntimeError, "changed during read-back verification"):
                _create_stable_source_snapshot(self.source, snapshot)

        self.assertFalse(snapshot.exists())
        self.assertEqual(self.source.read_bytes(), b"synthetic video")

    def test_snapshot_creation_rejects_short_writes_and_cleans_partial_snapshot(self):
        snapshot = self.root / "short-write-snapshot.mp4"
        real_open = Path.open

        class ShortWriteHandle:
            def __init__(self, handle):
                self.handle = handle

            def __enter__(self):
                self.handle.__enter__()
                return self

            def __exit__(self, exc_type, exc, traceback):
                return self.handle.__exit__(exc_type, exc, traceback)

            def write(self, data):
                return self.handle.write(data[:-1])

            def fileno(self):
                return self.handle.fileno()

            def flush(self):
                return self.handle.flush()

        def open_with_short_write(path, *args, **kwargs):
            handle = real_open(path, *args, **kwargs)
            if path == snapshot and args and args[0] == "xb":
                return ShortWriteHandle(handle)
            return handle

        with patch.object(Path, "open", new=open_with_short_write):
            with self.assertRaisesRegex(OSError, "short write while creating the source snapshot"):
                _create_stable_source_snapshot(self.source, snapshot)

        self.assertFalse(snapshot.exists())
        self.assertEqual(self.source.read_bytes(), b"synthetic video")

    def test_snapshot_creation_rejects_digest_mismatch_and_cleans_own_snapshot(self):
        snapshot = self.root / "mismatch-snapshot.mp4"
        with self.assertRaisesRegex(ValueError, "SHA-256 does not match"):
            _create_stable_source_snapshot(
                self.source, snapshot, expected_sha256="0" * 64
            )
        self.assertFalse(snapshot.exists())

    def test_sha256_selected_source_rejects_symbolic_link(self):
        link = self.root / "selected-link.mp4"
        try:
            link.symlink_to(self.source)
        except (OSError, NotImplementedError):
            self.skipTest("symbolic links are unavailable on this platform")
        with self.assertRaisesRegex(ValueError, "regular non-symlink"):
            sha256_selected_source(link)

    def test_candidate_csv_path_open_errors_return_controlled_value_error(self):
        pack = self.root / "candidate-path-open-error.csv"
        for error in (
            RuntimeError("candidate path conversion failed"),
            TypeError("candidate path conversion returned an invalid value"),
        ):
            with self.subTest(error_type=type(error).__name__):
                with patch(
                    "backend.app.single_clip_render.Path.open",
                    side_effect=error,
                ):
                    with self.assertRaisesRegex(
                        ValueError,
                        f"candidate CSV could not be read: {type(error).__name__}:",
                    ):
                        load_selected_candidate(pack, 1)

    def test_candidate_csv_path_with_embedded_nul_returns_controlled_value_error(self):
        with self.assertRaisesRegex(ValueError, "candidate CSV path could not be opened"):
            load_selected_candidate("invalid\x00candidate.csv", 1)

    def test_loads_exact_selected_review_ready_candidate(self):
        pack = self.root / "candidates.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,12.5,27.5,15.0,True\n",
            encoding="utf-8",
        )
        selected = load_selected_candidate(pack, 1)
        self.assertEqual(selected["source_id"], "authorized-demo")
        self.assertEqual(selected["start_seconds"], 12.5)
        self.assertEqual(selected["end_seconds"], 27.5)
        self.assertEqual(selected["row_number"], 1)

    def test_clip_pack_export_connects_to_exact_renderer_candidate_loader(self):
        origin = "2026-11-19T12:00:00+00:00"
        candidate = {
            "source_id": "authorized-demo",
            "score": 80,
            "peak_message_count": 24,
            "peak_window_start": "2026-11-19T12:00:40+00:00",
            "clip_start": "2026-11-19T12:00:30+00:00",
            "clip_end": "2026-11-19T12:00:45+00:00",
        }
        mapped_rows = map_candidates_to_media([candidate], origin)
        self.assertTrue(mapped_rows[0]["renderable"])
        csv_path, _ = write_clip_pack(mapped_rows, self.root / "clip-pack")
        selected = load_selected_candidate(csv_path, 1)
        self.assertEqual(selected["source_id"], candidate["source_id"])
        self.assertEqual(selected["start_seconds"], 30.0)
        self.assertEqual(selected["end_seconds"], 45.0)
        self.assertEqual(selected["duration_seconds"], 15.0)


    def test_candidate_csv_cli_records_exact_selected_row_in_dry_run_report(self):
        origin = "2026-11-19T12:00:00+00:00"
        candidate = {
            "source_id": "authorized-demo",
            "score": 80,
            "peak_message_count": 24,
            "peak_window_start": "2026-11-19T12:00:40+00:00",
            "clip_start": "2026-11-19T12:00:30+00:00",
            "clip_end": "2026-11-19T12:00:45+00:00",
        }
        mapped_rows = map_candidates_to_media([candidate], origin)
        csv_path, _ = write_clip_pack(mapped_rows, self.root / "cli-clip-pack")
        report_path = self.root / "cli-report.json"
        expected = {
            "status": "PLANNED",
            "upload_performed": False,
            "publishing_enabled": False,
        }
        argv = [
            "single_clip_render.py", str(self.source),
            "--candidate-csv", str(csv_path), "--candidate-row", "1",
            "--source-sha256", hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "--source-id", "authorized-demo", "--report", str(report_path),
        ]
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip", return_value=expected
        ) as render:
            self.assertEqual(main(), 0)
        render.assert_called_once()
        self.assertEqual(render.call_args.args[2:4], (30.0, 45.0))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["candidate_selection"]["source_id"], "authorized-demo")
        self.assertEqual(report["candidate_selection"]["row_number"], 1)
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])


    def test_candidate_cli_reserves_running_report_before_hashing_selected_media(self):
        pack = self.root / "reservation-order-pack"
        pack.mkdir()
        csv_path = pack / "candidates.csv"
        csv_path.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,2,8,6,True\n",
            encoding="utf-8",
        )
        report_path = self.root / "reservation-order-report.json"
        expected_digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        argv = [
            "single_clip_render.py", str(self.source),
            "--candidate-csv", str(csv_path), "--candidate-row", "1",
            "--source-sha256", expected_digest,
            "--source-id", "authorized-demo", "--report", str(report_path),
        ]

        def verify_hash_after_reservation(path):
            self.assertEqual(Path(path), self.source)
            self.assertTrue(report_path.exists())
            reserved = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(reserved["status"], "RUNNING")
            self.assertEqual(reserved["candidate_selection"]["source_id"], "authorized-demo")
            self.assertRegex(reserved["run_id"], r"^[0-9a-f]{32}$")
            self.assertTrue(reserved["started_at_utc"].endswith("+00:00"))
            self.assertIsInstance(reserved["process_id"], int)
            self.assertGreater(reserved["process_id"], 0)
            return expected_digest

        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.sha256_selected_source",
            side_effect=verify_hash_after_reservation,
        ) as source_hash, patch(
            "backend.app.single_clip_render.render_selected_clip",
            return_value={
                "status": "PLANNED",
                "upload_performed": False,
                "publishing_enabled": False,
            },
        ) as render:
            self.assertEqual(main(), 0)

        source_hash.assert_called_once_with(self.source)
        render.assert_called_once()
        terminal = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(
            terminal["candidate_selection"]["verified_source_sha256"],
            expected_digest,
        )
        self.assertRegex(terminal["run_id"], r"^[0-9a-f]{32}$")
        self.assertTrue(terminal["started_at_utc"].endswith("+00:00"))
        self.assertIsInstance(terminal["process_id"], int)
        self.assertGreater(terminal["process_id"], 0)

    def test_candidate_csv_cli_rejects_mismatched_source_id_before_report_reservation(self):
        mapped_rows = map_candidates_to_media(
            [{
                "source_id": "authorized-demo",
                "clip_start": "2026-11-19T12:00:30+00:00",
                "clip_end": "2026-11-19T12:00:45+00:00",
            }],
            "2026-11-19T12:00:00+00:00",
        )
        csv_path, _ = write_clip_pack(mapped_rows, self.root / "mismatch-pack")
        report_path = self.root / "mismatch-report.json"
        argv = [
            "single_clip_render.py", str(self.source),
            "--candidate-csv", str(csv_path), "--candidate-row", "1",
            "--source-sha256", hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "--source-id", "different-source", "--report", str(report_path),
        ]
        with patch("sys.argv", argv), self.assertRaises(SystemExit) as raised:
            main()
        self.assertEqual(raised.exception.code, 2)
        self.assertFalse(report_path.exists())



    def test_candidate_csv_cli_requires_nonblank_source_id_before_report_reservation(self):
        mapped_rows = map_candidates_to_media(
            [{
                "source_id": "authorized-demo",
                "clip_start": "2026-11-19T12:00:30+00:00",
                "clip_end": "2026-11-19T12:00:45+00:00",
            }],
            "2026-11-19T12:00:00+00:00",
        )
        csv_path, _ = write_clip_pack(mapped_rows, self.root / "missing-id-pack")
        for suffix, extra_args in (
            ("missing", []),
            ("blank", ["--source-id", "   "]),
        ):
            with self.subTest(source_id=suffix):
                report_path = self.root / f"{suffix}-source-id-report.json"
                argv = [
                    "single_clip_render.py", str(self.source),
                    "--candidate-csv", str(csv_path), "--candidate-row", "1",
                    "--source-sha256", hashlib.sha256(self.source.read_bytes()).hexdigest(),
                    *extra_args, "--report", str(report_path),
                ]
                with patch("sys.argv", argv), self.assertRaises(SystemExit) as raised:
                    main()
                self.assertEqual(raised.exception.code, 2)
                self.assertFalse(report_path.exists())


    def test_candidate_csv_cli_source_id_comparison_is_case_sensitive(self):
        mapped_rows = map_candidates_to_media(
            [{
                "source_id": "Authorized-Demo",
                "clip_start": "2026-11-19T12:00:30+00:00",
                "clip_end": "2026-11-19T12:00:45+00:00",
            }],
            "2026-11-19T12:00:00+00:00",
        )
        csv_path, _ = write_clip_pack(mapped_rows, self.root / "case-pack")
        report_path = self.root / "case-mismatch-report.json"
        argv = [
            "single_clip_render.py", str(self.source),
            "--candidate-csv", str(csv_path), "--candidate-row", "1",
            "--source-sha256", hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "--source-id", "authorized-demo", "--report", str(report_path),
        ]
        with patch("sys.argv", argv), self.assertRaises(SystemExit) as raised:
            main()
        self.assertEqual(raised.exception.code, 2)
        self.assertFalse(report_path.exists())


    def test_candidate_cli_rejects_invalid_trusted_sha256_before_report_reservation(self):
        mapped_rows = map_candidates_to_media(
            [{
                "source_id": "authorized-demo",
                "clip_start": "2026-11-19T12:00:30+00:00",
                "clip_end": "2026-11-19T12:00:45+00:00",
            }],
            "2026-11-19T12:00:00+00:00",
        )
        csv_path, _ = write_clip_pack(mapped_rows, self.root / "bad-digest-pack")
        report_path = self.root / "bad-digest-report.json"
        argv = [
            "single_clip_render.py", str(self.source),
            "--candidate-csv", str(csv_path), "--candidate-row", "1",
            "--source-id", "authorized-demo", "--source-sha256", "not-a-digest",
            "--report", str(report_path),
        ]
        with patch("sys.argv", argv), self.assertRaises(SystemExit) as raised:
            main()
        self.assertEqual(raised.exception.code, 2)
        self.assertFalse(report_path.exists())

    def test_source_id_option_is_rejected_in_direct_bounds_mode(self):
        report_path = self.root / "unexpected-source-id-report.json"
        with patch("sys.argv", [
            "single_clip_render.py", str(self.source),
            "--start", "1", "--end", "5", "--source-id", "authorized-demo",
            "--report", str(report_path),
        ]), self.assertRaises(SystemExit) as raised:
            main()
        self.assertEqual(raised.exception.code, 2)
        self.assertFalse(report_path.exists())

    def test_candidate_selection_rejects_unrenderable_row(self):
        pack = self.root / "candidates.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,12,27,15,False\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "not marked renderable"):
            load_selected_candidate(pack, 1)

    def test_candidate_selection_rejects_duration_mismatch(self):
        pack = self.root / "candidates.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,12,27,14,True\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "duration does not match"):
            load_selected_candidate(pack, 1)

    def test_candidate_selection_rejects_missing_source_identity(self):
        pack = self.root / "candidates.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            ",12,27,15,True\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "no source_id"):
            load_selected_candidate(pack, 1)

    def test_candidate_selection_rejects_nonexistent_row(self):
        pack = self.root / "candidates.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "does not exist"):
            load_selected_candidate(pack, 1)

    def test_cli_uses_explicit_reviewed_candidate_row(self):
        pack = self.root / "candidates.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,12.5,27.5,15.0,True\n",
            encoding="utf-8",
        )
        report_path = self.root / "report.json"
        with patch("sys.argv", [
            "single_clip_render", str(self.source),
            "--candidate-csv", str(pack), "--candidate-row", "1",
            "--source-sha256", hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "--source-id", "authorized-demo",
            "--output", str(self.output), "--report", str(report_path),
        ]):
            with patch(
                "backend.app.single_clip_render.render_selected_clip",
                return_value={
                    "status": "PLANNED", "start_seconds": 12.5, "end_seconds": 27.5,
                    "upload_performed": False, "publishing_enabled": False,
                },
            ) as render:
                self.assertEqual(main(), 0)
        self.assertEqual(render.call_args.args[2:4], (12.5, 27.5))
        saved = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["candidate_selection"]["source_id"], "authorized-demo")
        self.assertEqual(saved["candidate_selection"]["row_number"], 1)

    def test_candidate_cli_rejects_existing_output_before_hashing_source(self):
        pack = self.root / "candidates-existing-output.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,2,8,6,True\n",
            encoding="utf-8",
        )
        self.output.write_bytes(b"preserve existing output")
        report_path = self.root / "existing-output-report.json"
        argv = [
            "single_clip_render", str(self.source),
            "--candidate-csv", str(pack), "--candidate-row", "1",
            "--source-id", "authorized-demo", "--source-sha256", "a" * 64,
            "--output", str(self.output), "--report", str(report_path),
        ]
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.sha256_selected_source"
        ) as source_hash, patch(
            "backend.app.single_clip_render.render_selected_clip"
        ) as render:
            self.assertEqual(main(), 1)

        source_hash.assert_not_called()
        render.assert_not_called()
        saved = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["status"], "FAIL")
        self.assertIn("output already exists", saved["error"])
        self.assertEqual(self.output.read_bytes(), b"preserve existing output")

    def test_dry_run_reports_path_resolution_runtime_error(self):
        with patch("pathlib.Path.resolve", side_effect=RuntimeError("symlink loop")):
            report = render_selected_clip(self.source, self.output, 1, 4)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("output path could not be validated", report["error"])
        self.assertFalse(report["processing_started"])

    def test_cli_handles_path_resolution_runtime_error_without_leaving_report(self):
        report_path = self.root / "report.json"
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]):
            with patch("pathlib.Path.resolve", side_effect=RuntimeError("symlink loop")):
                self.assertEqual(main(), 2)
        self.assertFalse(report_path.exists())

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_dry_run_plans_exactly_one_clip_without_rendering(self, preflight):
        with patch("backend.app.single_clip_render.render_clip") as render:
            report = render_selected_clip(self.source, self.output, 2, 8)
        self.assertEqual(report["status"], "PLANNED")
        self.assertFalse(report["processing_started"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        render.assert_not_called()
        preflight.assert_called_once()
        inspected_source = preflight.call_args.args[0]
        self.assertEqual(inspected_source, self.source)
        self.assertFalse(report["source_snapshot_verified"])
        self.assertFalse(report["source_snapshot_created"])

    def test_renderer_rejects_invalid_video_path_types_before_path_conversion(self):
        invalid_paths = (None, 7, [], {}, "", "   ")
        for invalid_path in invalid_paths:
            with self.subTest(path_type=type(invalid_path).__name__, value=repr(invalid_path)):
                with patch("backend.app.single_clip_render.inspect_one_video") as preflight, patch(
                    "backend.app.single_clip_render._create_stable_source_snapshot"
                ) as snapshot:
                    report = render_selected_clip(invalid_path, self.output, 1, 5)
                self.assertEqual(report["status"], "FAIL")
                self.assertEqual(
                    report["error"],
                    "video_path must be a non-empty string or pathlib.Path",
                )
                self.assertFalse(report["processing_started"])
                preflight.assert_not_called()
                snapshot.assert_not_called()

    def test_renderer_rejects_invalid_output_path_types_before_path_conversion(self):
        invalid_paths = (None, 7, [], {}, "", "   ")
        for invalid_path in invalid_paths:
            with self.subTest(path_type=type(invalid_path).__name__, value=repr(invalid_path)):
                with patch("backend.app.single_clip_render.inspect_one_video") as preflight, patch(
                    "backend.app.single_clip_render._create_stable_source_snapshot"
                ) as snapshot:
                    report = render_selected_clip(self.source, invalid_path, 1, 5)
                self.assertEqual(report["status"], "FAIL")
                self.assertEqual(
                    report["error"],
                    "output_path must be a non-empty string or pathlib.Path",
                )
                self.assertFalse(report["processing_started"])
                preflight.assert_not_called()
                snapshot.assert_not_called()

    def test_dry_run_rejects_invalid_bounds_before_ffprobe(self):
        with patch("backend.app.single_clip_render.inspect_one_video") as preflight:
            report = render_selected_clip(self.source, self.output, "not-a-time", 4)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("clip bounds must be finite numbers", report["error"])
        self.assertFalse(report["processing_started"])
        preflight.assert_not_called()

    def test_rejects_unrepresentable_source_duration_without_crashing(self):
        invalid_preflight = {
            "status": "PASS",
            "duration_seconds": 10 ** 400,
            "video_streams": [{"codec": "h264"}],
        }
        with patch("backend.app.single_clip_render.inspect_one_video", return_value=invalid_preflight):
            with patch("backend.app.single_clip_render.render_clip") as render:
                report = render_selected_clip(self.source, self.output, 2, 8)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["error"], "source preflight did not provide a valid media duration")
        self.assertFalse(report["processing_started"])
        render.assert_not_called()

    def test_rejects_unrepresentable_rendered_duration_without_crashing(self):
        invalid_rendered_preflight = {
            "status": "PASS",
            "duration_seconds": 10 ** 400,
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            "video_streams": [{"codec": "h264", "width": 1080, "height": 1920}],
        }
        with patch(
            "backend.app.single_clip_render.inspect_one_video",
            side_effect=[PASS, invalid_rendered_preflight],
        ):
            with patch(
                "backend.app.single_clip_render.render_clip",
                return_value=self.output.resolve(),
            ) as render:
                report = render_selected_clip(
                    self.source, self.output, 2, 8,
                    execute=True, rights_confirmed=True,
                )
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(
            report["error"],
            "rendered output duration is outside the expected clip bounds",
        )
        self.assertTrue(report["processing_started"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        render.assert_called_once()


    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_dry_run_never_creates_a_source_snapshot(self, _preflight):
        with patch("backend.app.single_clip_render._create_stable_source_snapshot") as snapshot:
            report = render_selected_clip(self.source, self.output, 2, 8)
        self.assertEqual(report["status"], "PLANNED")
        self.assertFalse(report["source_snapshot_created"])
        snapshot.assert_not_called()

    def test_invalid_clip_bounds_fail_before_source_snapshot(self):
        invalid_bounds = [
            (True, 4),
            (1, False),
            ("not-a-time", 4),
            (1, "not-a-time"),
            (10 ** 10000, 10 ** 10000 + 1),
            (float("inf"), 4),
            (-1, 4),
            (4, 4),
            (1, 182),
        ]
        for start, end in invalid_bounds:
            with self.subTest(start_type=type(start).__name__, end_type=type(end).__name__):
                with patch("backend.app.single_clip_render._create_stable_source_snapshot") as snapshot:
                    with patch("backend.app.single_clip_render.inspect_one_video") as preflight:
                        report = render_selected_clip(
                            self.source, self.output, start, end,
                            execute=True, rights_confirmed=True,
                        )
                self.assertEqual(report["status"], "FAIL")
                self.assertFalse(report["processing_started"])
                self.assertFalse(report["source_snapshot_created"])
                snapshot.assert_not_called()
                preflight.assert_not_called()

    def test_refuses_source_mutation_during_preflight(self):
        def mutate_selected_source(path, *, ffprobe_binary):
            path.write_bytes(b"replacement video bytes")
            return PASS

        with patch("backend.app.single_clip_render.inspect_one_video", side_effect=mutate_selected_source):
            with patch("backend.app.single_clip_render.render_clip") as render:
                report = render_selected_clip(self.source, self.output, 2, 8, execute=True, rights_confirmed=True)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("changed during preflight", report["error"])
        self.assertFalse(report["processing_started"])
        self.assertFalse(report["source_identity_verified"])
        render.assert_not_called()

    def test_execution_rejects_existing_output_before_source_snapshot(self):
        self.output.write_bytes(b"preserve existing output")
        with patch("backend.app.single_clip_render._create_stable_source_snapshot") as snapshot:
            report = render_selected_clip(
                self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("never overwritten", report["error"])
        self.assertFalse(report["processing_started"])
        self.assertFalse(report["source_snapshot_created"])
        snapshot.assert_not_called()
        self.assertEqual(self.output.read_bytes(), b"preserve existing output")

    def test_execution_rejects_symlink_output_before_source_snapshot(self):
        target = self.root / "redirected.mp4"
        try:
            self.output.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable on this runner")
        with patch("backend.app.single_clip_render._create_stable_source_snapshot") as snapshot:
            report = render_selected_clip(
                self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("symbolic link", report["error"])
        self.assertFalse(report["processing_started"])
        snapshot.assert_not_called()
        self.assertFalse(target.exists())
        self.assertTrue(self.output.is_symlink())

    def test_execution_requires_rights_confirmation_before_any_media_inspection(self):
        with patch("backend.app.single_clip_render.inspect_one_video") as preflight, patch(
            "backend.app.single_clip_render.sha256_selected_source"
        ) as source_hash, patch(
            "backend.app.single_clip_render._create_stable_source_snapshot"
        ) as snapshot, patch("backend.app.single_clip_render.render_clip") as render:
            report = render_selected_clip(self.source, self.output, 2, 8, execute=True)

        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["error"], "render execution requires --confirm-rights")
        self.assertFalse(report["processing_started"])
        self.assertFalse(report["source_snapshot_created"])
        preflight.assert_not_called()
        source_hash.assert_not_called()
        snapshot.assert_not_called()
        render.assert_not_called()

    def test_candidate_cli_without_rights_confirmation_does_not_hash_or_probe_media(self):
        report_path = self.root / "candidate-blocked-report.json"
        csv_path = self.root / "candidates.csv"
        csv_path.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\\n"
            "authorized-demo,1,5,4,True\\n",
            encoding="utf-8",
        )
        expected_digest = "a" * 64
        argv = [
            "single_clip_render.py", str(self.source),
            "--candidate-csv", str(csv_path), "--candidate-row", "1",
            "--source-id", "authorized-demo", "--source-sha256", expected_digest,
            "--execute", "--output", str(self.output), "--report", str(report_path),
        ]
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.sha256_selected_source"
        ) as source_hash, patch(
            "backend.app.single_clip_render.inspect_one_video"
        ) as preflight:
            self.assertEqual(main(), 1)

        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "BLOCKED")
        self.assertTrue(report["execution_requested"])
        self.assertFalse(report["rights_confirmation_supplied"])
        source_hash.assert_not_called()
        preflight.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_render_api_rejects_malformed_expected_digest_before_media_tools(self):
        with patch("backend.app.single_clip_render.inspect_one_video") as preflight, patch(
            "backend.app.single_clip_render._create_stable_source_snapshot"
        ) as snapshot:
            report = render_selected_clip(
                self.source, self.output, 2, 8,
                execute=True, rights_confirmed=True,
                expected_source_sha256="not-a-sha256",
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("64 lowercase hexadecimal", report["error"])
        self.assertFalse(report["source_snapshot_created"])
        self.assertFalse(report["source_snapshot_verified"])
        self.assertIsNone(report["source_sha256"])
        preflight.assert_not_called()
        snapshot.assert_not_called()
        self.assertFalse(self.output.exists())

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    @patch("backend.app.single_clip_render.render_clip")
    def test_preflight_and_renderer_consume_the_same_snapshot(self, render, preflight):
        render.side_effect = lambda *args, **kwargs: (self.output.write_bytes(b"rendered mp4"), self.output.resolve())[1]
        preflight.side_effect = [PASS, {"status": "PASS", "duration_seconds": 6.0, "format_name": "mov,mp4,m4a,3gp,3g2,mj2", "video_streams": [{"codec": "h264", "width": 1080, "height": 1920}]}]
        expected = hashlib.sha256(self.source.read_bytes()).hexdigest()
        report = render_selected_clip(
            self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
            expected_source_sha256=expected,
        )
        self.assertEqual(report["status"], "RENDERED")
        inspected_path = preflight.call_args_list[0].args[0]
        rendered_path = render.call_args.args[0]
        self.assertEqual(inspected_path, rendered_path)
        self.assertNotEqual(inspected_path, self.source)
        self.assertTrue(report["source_snapshot_verified"])
        self.assertEqual(report["source_sha256"], expected)

    @patch("backend.app.single_clip_render.inspect_one_video")
    @patch("backend.app.single_clip_render.render_clip")
    def test_execution_digest_mismatch_stops_before_ffprobe_or_ffmpeg(self, render, preflight):
        expected = "0" * 64
        report = render_selected_clip(
            self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
            expected_source_sha256=expected,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("SHA-256 does not match", report["error"])
        self.assertFalse(report["source_snapshot_created"])
        self.assertFalse(report["source_snapshot_verified"])
        self.assertEqual(report["expected_source_sha256"], expected)
        self.assertIsNone(report["source_sha256"])
        preflight.assert_not_called()
        render.assert_not_called()
        self.assertFalse(self.output.exists())

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    @patch("backend.app.single_clip_render.render_clip")
    def test_render_exception_preserves_possible_output_and_requires_inspection(self, render, _preflight):
        payload = b"output linked before cleanup failure"
        def create_output_then_fail(*args, **kwargs):
            self.output.write_bytes(payload)
            raise OSError("simulated temporary-directory cleanup failure")

        render.side_effect = create_output_then_fail
        report = render_selected_clip(
            self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("cleanup failure", report["error"])
        self.assertTrue(report["output_inspection_required"])
        self.assertIn("Inspect the configured output path before retrying", report["message"])
        self.assertIsNone(report["processing_started"])
        self.assertEqual(self.output.read_bytes(), payload)
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        render.assert_called_once()


    @patch("backend.app.single_clip_render.inspect_one_video")
    @patch("backend.app.single_clip_render.render_clip")
    def test_ffprobe_exception_after_render_requires_manual_output_inspection(self, render, preflight):
        payload = b"rendered output whose ffprobe process failed"
        render.side_effect = lambda *args, **kwargs: (
            self.output.write_bytes(payload), self.output.resolve()
        )[1]
        preflight.side_effect = [
            PASS,
            RuntimeError("simulated ffprobe process failure"),
        ]

        report = render_selected_clip(
            self.source, self.output, 2, 8,
            execute=True, rights_confirmed=True,
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["output_path"], str(self.output.resolve()))
        self.assertIn("RuntimeError: simulated ffprobe process failure", report["rendered_preflight_error"])
        self.assertTrue(report["output_inspection_required"])
        self.assertTrue(report["manual_cleanup_required"])
        self.assertIn("Inspect this exact output path before retrying", report["message"])
        self.assertTrue(report["processing_started"])
        self.assertEqual(self.output.read_bytes(), payload)
        self.assertNotIn("output_sha256", report)
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        self.assertEqual(preflight.call_count, 2)


    @patch("backend.app.single_clip_render.inspect_one_video")
    @patch("backend.app.single_clip_render.render_clip")
    def test_malformed_ffprobe_metadata_after_render_requires_manual_inspection(self, render, preflight):
        payload = b"rendered output with malformed ffprobe metadata"
        render.side_effect = lambda *args, **kwargs: (
            self.output.write_bytes(payload), self.output.resolve()
        )[1]
        preflight.side_effect = [PASS, ["unexpected", "list", "payload"]]

        report = render_selected_clip(
            self.source, self.output, 2, 8,
            execute=True, rights_confirmed=True,
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["output_path"], str(self.output.resolve()))
        self.assertIn("expected an object", report["rendered_preflight_error"])
        self.assertIn("list", report["rendered_preflight_error"])
        self.assertTrue(report["output_inspection_required"])
        self.assertTrue(report["manual_cleanup_required"])
        self.assertIn("malformed metadata", report["message"])
        self.assertTrue(report["processing_started"])
        self.assertEqual(self.output.read_bytes(), payload)
        self.assertNotIn("output_sha256", report)
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        self.assertEqual(preflight.call_count, 2)


    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    @patch("backend.app.single_clip_render.render_clip")
    def test_renders_one_clip_and_verifies_output(self, render, preflight):
        payload = b"verified rendered mp4 bytes"
        rendered = self.output.resolve()
        def create_rendered_output(*args, **kwargs):
            self.output.write_bytes(payload)
            return rendered
        render.side_effect = create_rendered_output
        preflight.side_effect = [PASS, {"status": "PASS", "duration_seconds": 6.0, "format_name": "mov,mp4,m4a,3gp,3g2,mj2", "video_streams": [{"codec": "h264", "width": 1080, "height": 1920}]}]
        report = render_selected_clip(
            self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "RENDERED")
        self.assertTrue(report["processing_started"])
        self.assertTrue(report["output_identity_verified"])
        self.assertEqual(report["output_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(report["output_size_bytes"], len(payload))
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        render.assert_called_once()
        self.assertEqual(preflight.call_count, 2)


    @patch("backend.app.single_clip_render.inspect_one_video")
    @patch("backend.app.single_clip_render.render_clip")
    def test_rejects_rendered_output_with_non_mp4_container(self, render, preflight):
        render.side_effect = lambda *args, **kwargs: (self.output.write_bytes(b"rendered"), self.output.resolve())[1]
        invalid = dict(PASS, duration_seconds=6.0, format_name="matroska,webm")
        preflight.side_effect = [PASS, invalid]
        report = render_selected_clip(
            self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("not identified as an MP4", report["error"])
        self.assertTrue(report["manual_cleanup_required"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])

    @patch("backend.app.single_clip_render.inspect_one_video")
    @patch("backend.app.single_clip_render.render_clip")
    def test_rejects_rendered_output_with_non_h264_video(self, render, preflight):
        render.side_effect = lambda *args, **kwargs: (self.output.write_bytes(b"rendered"), self.output.resolve())[1]
        invalid = dict(PASS, duration_seconds=6.0, video_streams=[{"codec": "vp9", "width": 1080, "height": 1920}])
        preflight.side_effect = [PASS, invalid]
        report = render_selected_clip(
            self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("codec is not H.264", report["error"])
        self.assertTrue(report["manual_cleanup_required"])


    def test_rendered_mp4_validation_accepts_h264_video_with_dimensions(self):
        valid = {
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            "video_streams": [{"codec": "h264", "width": 1080, "height": 1920}],
        }
        self.assertIsNone(_rendered_mp4_validation_error(valid))

    def test_rendered_mp4_validation_rejects_landscape_output(self):
        invalid = {
            "format_name": "mp4",
            "video_streams": [{"codec": "h264", "width": 1920, "height": 1080}],
        }
        self.assertEqual(
            _rendered_mp4_validation_error(invalid),
            "rendered output video stream 0 must be exactly 1080x1920 portrait",
        )

    def test_rendered_mp4_validation_rejects_nonstandard_portrait_dimensions(self):
        invalid = {
            "format_name": "mp4",
            "video_streams": [{"codec": "h264", "width": 720, "height": 1280}],
        }
        self.assertEqual(
            _rendered_mp4_validation_error(invalid),
            "rendered output video stream 0 must be exactly 1080x1920 portrait",
        )

    def test_rendered_mp4_validation_rejects_missing_video_stream(self):
        invalid = {"format_name": "mp4", "video_streams": []}
        self.assertEqual(
            _rendered_mp4_validation_error(invalid),
            "rendered output has no verified video stream",
        )

    def test_rendered_mp4_validation_checks_every_video_stream(self):
        invalid = {
            "format_name": "mp4",
            "video_streams": [
                {"codec": "h264", "width": 1080, "height": 1920},
                {"codec": "vp9", "width": 1080, "height": 1920},
            ],
        }
        self.assertEqual(
            _rendered_mp4_validation_error(invalid),
            "rendered output video codec is not H.264",
        )

    def test_rendered_mp4_validation_rejects_malformed_secondary_stream(self):
        invalid = {
            "format_name": "mp4",
            "video_streams": [
                {"codec": "h264", "width": 1080, "height": 1920},
                None,
            ],
        }
        self.assertEqual(
            _rendered_mp4_validation_error(invalid),
            "rendered output video stream 1 metadata is invalid",
        )

    def test_rendered_mp4_validation_rejects_missing_or_boolean_dimensions(self):
        cases = [
            ({"codec": "h264", "height": 1080}, "width"),
            ({"codec": "h264", "width": 1920, "height": True}, "height"),
            ({"codec": "h264", "width": 0, "height": 1080}, "width"),
        ]
        for stream, dimension in cases:
            with self.subTest(stream=stream):
                invalid = {"format_name": "mp4", "video_streams": [stream]}
                self.assertEqual(
                    _rendered_mp4_validation_error(invalid),
                    f"rendered output has invalid video {dimension}",
                )

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_rejects_end_beyond_selected_source_duration(self, _preflight):
        report = render_selected_clip(self.source, self.output, 15, 21)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("exceeds", report["error"])

    @patch("backend.app.single_clip_render.inspect_one_video", return_value={"status": "FAIL", "error": "bad input"})
    def test_rejects_source_that_fails_preflight(self, preflight):
        report = render_selected_clip(self.source, self.output, 1, 4)
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["processing_started"])
        preflight.assert_called_once()

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_rejects_invalid_and_overlong_bounds(self, _preflight):
        for start, end in ((-1, 2), (4, 4), (0, 181), (float("nan"), 3)):
            with self.subTest(start=start, end=end):
                report = render_selected_clip(self.source, self.output, start, end)
                self.assertEqual(report["status"], "FAIL")

    @patch("backend.app.single_clip_render.inspect_one_video")
    @patch("backend.app.single_clip_render.render_clip")
    def test_rejects_same_size_output_path_replacement_after_ffprobe(self, render, preflight):
        original = b"original rendered payload"
        replacement = b"replacement rendered data"
        self.assertEqual(len(original), len(replacement))

        def create_output(*args, **kwargs):
            self.output.write_bytes(original)
            return self.output.resolve()

        def replace_during_output_probe(path, **kwargs):
            if Path(path) == self.output.resolve():
                displaced = self.root / "displaced-original.mp4"
                self.output.rename(displaced)
                self.output.write_bytes(replacement)
                return {
                    "status": "PASS",
                    "duration_seconds": 6.0,
                    "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                    "video_streams": [{"codec": "h264", "width": 1080, "height": 1920}],
                }
            return PASS

        render.side_effect = create_output
        preflight.side_effect = replace_during_output_probe
        report = render_selected_clip(
            self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("final identity/SHA-256 verification", report["error"])
        self.assertIsNone(report["output_sha256"])
        self.assertTrue(report["manual_cleanup_required"])
        self.assertEqual(self.output.read_bytes(), replacement)
        self.assertEqual((self.root / "displaced-original.mp4").read_bytes(), original)

    @patch("backend.app.single_clip_render.inspect_one_video")
    @patch("backend.app.single_clip_render.render_clip")
    def test_rejects_output_mutated_after_ffprobe_before_final_hash(self, render, preflight):
        payload = b"rendered output before probe"
        def create_output(*args, **kwargs):
            self.output.write_bytes(payload)
            return self.output.resolve()
        def mutate_during_output_probe(path, **kwargs):
            if Path(path) == self.output.resolve():
                self.output.write_bytes(b"changed after probe with different length")
                return {"status": "PASS", "duration_seconds": 6.0, "format_name": "mov,mp4,m4a,3gp,3g2,mj2", "video_streams": [{"codec": "h264", "width": 1080, "height": 1920}]}
            return PASS
        render.side_effect = create_output
        preflight.side_effect = mutate_during_output_probe
        report = render_selected_clip(
            self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("final identity/SHA-256 verification", report["error"])
        self.assertIsNone(report["output_sha256"])
        self.assertTrue(report["manual_cleanup_required"])
        self.assertEqual(self.output.read_bytes(), b"changed after probe with different length")

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    @patch("backend.app.single_clip_render.render_clip")
    def test_rejects_unexpectedly_short_rendered_output(self, render, preflight):
        render.side_effect = lambda *args, **kwargs: (self.output.write_bytes(b"rendered mp4"), self.output.resolve())[1]
        preflight.side_effect = [PASS, {"status": "PASS", "duration_seconds": 1.0, "format_name": "mov,mp4,m4a,3gp,3g2,mj2", "video_streams": [{"codec": "h264", "width": 1080, "height": 1920}]}]
        report = render_selected_clip(
            self.source, self.output, 2, 8, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("expected clip bounds", report["error"])

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    @patch("backend.app.single_clip_render.render_clip")
    def test_rejects_nearly_empty_output_for_short_clip(self, render, preflight):
        render.side_effect = lambda *args, **kwargs: (self.output.write_bytes(b"rendered mp4"), self.output.resolve())[1]
        preflight.side_effect = [PASS, {"status": "PASS", "duration_seconds": 0.01, "format_name": "mov,mp4,m4a,3gp,3g2,mj2", "video_streams": [{"codec": "h264", "width": 1080, "height": 1920}]}]
        report = render_selected_clip(
            self.source, self.output, 2, 2.1, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("expected clip bounds", report["error"])

    @patch("backend.app.single_clip_render.inspect_one_video")
    @patch("backend.app.single_clip_render.render_clip")
    def test_preserves_own_unverified_output_for_manual_cleanup(self, render, preflight):
        payload = b"unverified render"
        render.side_effect = lambda *args, **kwargs: (
            self.output.write_bytes(payload) and self.output.resolve()
        )
        preflight.side_effect = [PASS, {"status": "FAIL", "error": "invalid output"}]
        with patch.object(Path, "unlink", wraps=Path.unlink) as unlink:
            report = render_selected_clip(
                self.source, self.output, 1, 5, execute=True, rights_confirmed=True,
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["unverified_output_removed"])
        self.assertTrue(report["manual_cleanup_required"])
        self.assertEqual(self.output.read_bytes(), payload)
        unlink.assert_not_called()

    @patch("backend.app.single_clip_render.inspect_one_video")
    @patch("backend.app.single_clip_render.render_clip")
    def test_preserves_replaced_output_when_post_render_ffprobe_fails(self, render, preflight):
        replacement = b"replacement must not be deleted"
        def render_own_file(*args, **kwargs):
            self.output.write_bytes(b"our unverified render")
            return self.output.resolve()
        def replace_during_verification(path, **kwargs):
            original_output = self.root / "original-unverified.mp4"
            self.output.rename(original_output)
            self.output.write_bytes(replacement)
            return {"status": "FAIL", "error": "invalid output"}
        render.side_effect = render_own_file
        preflight.side_effect = [PASS, replace_during_verification]
        report = render_selected_clip(
            self.source, self.output, 1, 5, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["unverified_output_removed"])
        self.assertEqual(self.output.read_bytes(), replacement)

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    @patch("backend.app.single_clip_render.render_clip")
    def test_rejects_output_that_fails_post_render_verification(self, render, preflight):
        render.side_effect = lambda *args, **kwargs: (self.output.write_bytes(b"rendered mp4"), self.output.resolve())[1]
        preflight.side_effect = [PASS, {"status": "FAIL", "error": "invalid output"}]
        report = render_selected_clip(
            self.source, self.output, 1, 5, execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("FFprobe verification", report["error"])

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_rejects_same_source_and_non_mp4_output_paths(self, _preflight):
        same = render_selected_clip(self.source, self.source, 1, 4)
        wrong_extension = render_selected_clip(self.source, self.root / "clip.mov", 1, 4)
        self.assertEqual(same["status"], "FAIL")
        self.assertIn("differ", same["error"])
        self.assertEqual(wrong_extension["status"], "FAIL")
        self.assertIn(".mp4", wrong_extension["error"])

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_refuses_existing_output_even_during_dry_run(self, _preflight):
        self.output.write_bytes(b"preserve me")
        report = render_selected_clip(self.source, self.output, 1, 4)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("never overwritten", report["error"])
        self.assertEqual(self.output.read_bytes(), b"preserve me")

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_dry_run_rejects_dangling_symlink_output(self, preflight):
        target = self.root / "redirected.mp4"
        try:
            self.output.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable on this runner")
        report = render_selected_clip(self.source, self.output, 1, 4)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("symbolic link", report["error"])
        self.assertFalse(target.exists())
        preflight.assert_not_called()

    def test_cli_existing_report_blocks_before_render_and_preserves_file(self):
        report_path = self.root / "report.json"
        report_path.write_text("keep this report", encoding="utf-8")
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
            "--execute", "--confirm-rights",
        ]):
            with patch("backend.app.single_clip_render.render_selected_clip") as render:
                self.assertEqual(main(), 2)
        render.assert_not_called()
        self.assertEqual(report_path.read_text(encoding="utf-8"), "keep this report")
        self.assertFalse(self.output.exists())

    def test_cli_report_path_cannot_alias_source_or_output(self):
        for report_path in (self.source, self.output):
            with self.subTest(report_path=report_path):
                with patch("sys.argv", [
                    "single_clip_render", str(self.source), "--start", "1", "--end", "5",
                    "--output", str(self.output), "--report", str(report_path),
                    "--execute", "--confirm-rights",
                ]):
                    with patch("backend.app.single_clip_render.render_selected_clip") as render:
                        self.assertEqual(main(), 2)
                render.assert_not_called()
                self.assertFalse(self.output.exists())

    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_cli_writes_exclusive_dry_run_report(self, _preflight):
        report_path = self.root / "report.json"
        stdout = io.StringIO()
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]), redirect_stdout(stdout):
            self.assertEqual(main(), 0)
        self.assertTrue(report_path.is_file())
        report_text = report_path.read_text(encoding="utf-8")
        self.assertEqual(stdout.getvalue(), report_text)
        self.assertTrue(report_text.endswith("\n"))
        self.assertEqual(json.loads(report_text)["status"], "PLANNED")
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]):
            self.assertEqual(main(), 2)


    def test_cli_rejects_non_finite_clip_bounds_before_report_reservation(self):
        for start, end in (("nan", "5"), ("1", "inf"), ("-inf", "5")):
            with self.subTest(start=start, end=end):
                report_path = self.root / f"non-finite-{start}-{end}.json"
                argv = [
                    "single_clip_render.py", str(self.source),
                    "--start", start, "--end", end,
                    "--output", str(self.output), "--report", str(report_path),
                ]
                with patch("sys.argv", argv):
                    with self.assertRaises(SystemExit) as raised:
                        main()
                self.assertEqual(raised.exception.code, 2)
                self.assertFalse(report_path.exists())
                self.assertFalse(self.output.exists())


    def test_cli_preserves_strict_running_report_when_terminal_json_contains_nan(self):
        report_path = self.root / "non-finite-terminal-report.json"
        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "2", "--end", "8",
            "--output", str(self.output), "--report", str(report_path),
        ]

        def reject_nonstandard_constant(value):
            raise ValueError(f"non-standard JSON constant: {value}")

        def completed_render_with_invalid_metadata(*args, **kwargs):
            self.output.write_bytes(b"completed synthetic render")
            return {
                "status": "RENDERED",
                "output_path": str(self.output),
                "unexpected_metadata": float("nan"),
                "upload_performed": False,
                "publishing_enabled": False,
            }

        stderr = io.StringIO()
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip",
            side_effect=completed_render_with_invalid_metadata,
        ) as render, redirect_stderr(stderr):
            self.assertEqual(main(), 2)

        self.assertTrue(report_path.exists())
        persisted = json.loads(
            report_path.read_text(encoding="utf-8"),
            parse_constant=reject_nonstandard_constant,
        )
        self.assertEqual(persisted["status"], "RUNNING")
        self.assertTrue(self.output.exists())
        self.assertEqual(self.output.read_bytes(), b"completed synthetic render")
        fallback_path = report_path.with_name(report_path.name + ".terminal-fallback.json")
        fallback = json.loads(
            fallback_path.read_text(encoding="utf-8"),
            parse_constant=reject_nonstandard_constant,
        )
        self.assertEqual(fallback["status"], "FAIL")
        self.assertTrue(fallback["terminal_report_serialization_failed"])
        self.assertEqual(fallback["render_result_status"], "RENDERED")
        self.assertTrue(fallback["output_inspection_required"])
        self.assertIn("Inspect any output file manually before retrying", fallback["message"])
        self.assertIn("Inspect any output file manually before retrying", stderr.getvalue())
        render.assert_called_once()


    def test_cli_handles_path_resolution_value_error_without_leaving_report(self):
        report_path = self.root / "report.json"
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]):
            with patch("pathlib.Path.resolve", side_effect=ValueError("invalid path")):
                self.assertEqual(main(), 2)
        self.assertFalse(report_path.exists())

    def test_snapshot_fails_closed_on_in_place_mutation_during_copy(self):
        source = self.root / "changing-source.mp4"
        snapshot = self.root / "snapshot.mp4"
        source.write_bytes(b"A" * (2 * 1024 * 1024))
        real_fdopen = __import__("os").fdopen

        class MutatingReader:
            def __init__(self, handle):
                self.handle = handle
                self.changed = False

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                self.handle.close()

            def read(self, size=-1):
                data = self.handle.read(size)
                if not self.changed:
                    self.changed = True
                    source.write_bytes(b"B" * (2 * 1024 * 1024))
                return data

        def fdopen_and_mutate(descriptor, mode):
            return MutatingReader(real_fdopen(descriptor, mode))

        with patch("backend.app.single_clip_render.os.fdopen", side_effect=fdopen_and_mutate):
            with self.assertRaisesRegex(RuntimeError, "changed while its stable snapshot was copied"):
                _create_stable_source_snapshot(source, snapshot)

        self.assertFalse(snapshot.exists())
        self.assertEqual(source.read_bytes(), b"B" * (2 * 1024 * 1024))

    def test_snapshot_rejects_symlink_source_before_creating_snapshot(self):
        target = self.root / "actual-source.mp4"
        selected = self.root / "selected-link.mp4"
        snapshot = self.root / "snapshot.mp4"
        target.write_bytes(b"authorized source bytes")
        try:
            selected.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable on this runner")

        with self.assertRaisesRegex(ValueError, "regular non-symlink"):
            _create_stable_source_snapshot(selected, snapshot)

        self.assertFalse(snapshot.exists())
        self.assertTrue(selected.is_symlink())


    def test_snapshot_fails_closed_when_selected_path_is_replaced_during_copy(self):
        source = self.root / "replaced-source.mp4"
        original = self.root / "original-source.mp4"
        replacement = self.root / "replacement-source.mp4"
        snapshot = self.root / "snapshot-replaced.mp4"
        original_bytes = b"original selected bytes" * 100
        replacement_bytes = b"replacement bytes must not be accepted"
        source.write_bytes(original_bytes)
        replacement.write_bytes(replacement_bytes)
        real_fdopen = __import__("os").fdopen

        class ReplacingReader:
            def __init__(self, handle):
                self.handle = handle
                self.replaced = False

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                self.handle.close()

            def read(self, size=-1):
                data = self.handle.read(size)
                if not self.replaced:
                    self.replaced = True
                    source.rename(original)
                    replacement.rename(source)
                return data

        def fdopen_and_replace(descriptor, mode):
            return ReplacingReader(real_fdopen(descriptor, mode))

        with patch("backend.app.single_clip_render.os.fdopen", side_effect=fdopen_and_replace):
            with self.assertRaisesRegex(RuntimeError, "changed while its stable snapshot was copied"):
                _create_stable_source_snapshot(source, snapshot)

        self.assertFalse(snapshot.exists())
        self.assertEqual(original.read_bytes(), original_bytes)
        self.assertEqual(source.read_bytes(), replacement_bytes)


    def test_snapshot_refuses_source_destination_alias_without_deleting_source(self):
        source = self.root / "same-file.mp4"
        original = b"do not delete the selected source"
        source.write_bytes(original)

        with self.assertRaisesRegex(ValueError, "destination must differ"):
            _create_stable_source_snapshot(source, source)

        self.assertEqual(source.read_bytes(), original)

    def test_snapshot_preserves_preexisting_destination_on_exclusive_create_failure(self):
        source = self.root / "snapshot-source.mp4"
        snapshot = self.root / "already-existing-snapshot.mp4"
        source.write_bytes(b"selected source")
        existing = b"pre-existing destination must survive"
        snapshot.write_bytes(existing)

        with self.assertRaises(FileExistsError):
            _create_stable_source_snapshot(source, snapshot)

        self.assertEqual(snapshot.read_bytes(), existing)
        self.assertEqual(source.read_bytes(), b"selected source")


    def test_cli_unexpected_python_exception_writes_terminal_failure_report(self):
        report_path = self.root / "terminal-unexpected-failure.json"
        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "2", "--end", "8",
            "--execute", "--confirm-rights",
            "--report", str(report_path),
        ]
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip",
            side_effect=TypeError("unexpected renderer boundary error"),
        ):
            self.assertEqual(main(), 1)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("unexpected renderer boundary error", report["error"])
        # The whole renderer raised before returning structured evidence.
        # Snapshot state is unknown here, not proven false.
        self.assertIsNone(report["source_snapshot_verified"])
        self.assertIsNone(report["source_snapshot_created"])
        self.assertIsNone(report["source_sha256"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])

    def test_cli_terminal_serialization_failure_preserves_parseable_running_report(self):
        report_path = self.root / "terminal-serialization-failure.json"
        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "2", "--end", "8",
            "--report", str(report_path),
        ]
        original_dumps = json.dumps
        calls = {"count": 0}

        def fail_terminal_serialization(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 2:
                raise TypeError("simulated terminal serialization failure")
            return original_dumps(*args, **kwargs)

        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip",
            return_value={"status": "PLANNED", "upload_performed": False,
                          "publishing_enabled": False},
        ), patch(
            "backend.app.single_clip_render.json.dumps",
            side_effect=fail_terminal_serialization,
        ):
            self.assertEqual(main(), 2)

        report_text = report_path.read_text(encoding="utf-8")
        self.assertTrue(report_text.endswith("\n"))
        report = json.loads(report_text)
        self.assertEqual(report["status"], "RUNNING")
        self.assertIn("not yet been recorded", report["message"])

    def test_cli_partial_initial_running_report_write_uses_fallback_and_skips_media(self):
        report_path = self.root / "partial-initial-report.json"
        original_open = Path.open

        class FailingWriteProxy:
            def __init__(self, handle):
                self.handle = handle

            def __enter__(self):
                self.handle.__enter__()
                return self

            def __exit__(self, *args):
                return self.handle.__exit__(*args)

            def __getattr__(self, name):
                return getattr(self.handle, name)

            def write(self, value):
                self.handle.write(value[:12])
                raise OSError("simulated partial initial report write")

        def open_with_initial_write_failure(path, *args, **kwargs):
            handle = original_open(path, *args, **kwargs)
            if path == report_path:
                return FailingWriteProxy(handle)
            return handle

        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "2", "--end", "8",
            "--execute", "--confirm-rights",
            "--output", str(self.output), "--report", str(report_path),
        ]
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip"
        ) as render, patch.object(
            Path, "open", new=open_with_initial_write_failure
        ):
            self.assertEqual(main(), 2)

        render.assert_not_called()
        fallback_path = report_path.with_name(report_path.name + ".terminal-fallback.json")
        fallback = json.loads(fallback_path.read_text(encoding="utf-8"))
        self.assertEqual(fallback["status"], "RUNNING")
        self.assertFalse(self.output.exists())

    def test_cli_terminal_report_fsync_failure_preserves_output_and_writes_fallback(self):
        report_path = self.root / "terminal-fsync-failure.json"
        fallback_path = report_path.with_name(
            report_path.name + ".terminal-fallback.json"
        )
        original_fsync = os.fsync
        fsync_calls = 0

        def fail_terminal_report_fsync(descriptor):
            nonlocal fsync_calls
            fsync_calls += 1
            # Count file fsync calls only; directory durability is covered
            # independently and its implementation differs on Windows.
            # Fail the second file sync, after the RUNNING reservation.
            if fsync_calls == 2:
                raise OSError("simulated terminal report fsync failure")
            return original_fsync(descriptor)

        def simulated_completed_render(*args, **kwargs):
            self.output.write_bytes(b"completed render output")
            return {
                "status": "RENDERED",
                "output_path": str(self.output),
                "upload_performed": False,
                "publishing_enabled": False,
            }

        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "2", "--end", "8",
            "--execute", "--confirm-rights",
            "--output", str(self.output), "--report", str(report_path),
        ]
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip",
            side_effect=simulated_completed_render,
        ), patch("backend.app.single_clip_render.os.fsync", side_effect=fail_terminal_report_fsync), patch(
            "backend.app.single_clip_render._fsync_parent_directory"
        ), redirect_stderr(io.StringIO()):
            self.assertEqual(main(), 2)

        self.assertEqual(fsync_calls, 3)
        self.assertEqual(self.output.read_bytes(), b"completed render output")
        # The primary report may contain the previous RUNNING record because
        # terminal contents were not confirmed durable.
        primary = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(primary["status"], "RUNNING")
        fallback = json.loads(fallback_path.read_text(encoding="utf-8"))
        self.assertEqual(fallback["status"], "RENDERED")
        self.assertFalse(fallback["upload_performed"])
        self.assertFalse(fallback["publishing_enabled"])

    def test_cli_partial_terminal_report_write_preserves_rendered_output_for_manual_review(self):
        report_path = self.root / "partial-terminal-write.json"
        original_open = Path.open

        class FailingWriteProxy:
            def __init__(self, handle):
                self.handle = handle
                self.write_calls = 0

            def __enter__(self):
                self.handle.__enter__()
                return self

            def __exit__(self, *args):
                return self.handle.__exit__(*args)

            def __getattr__(self, name):
                return getattr(self.handle, name)

            def write(self, value):
                self.write_calls += 1
                if self.write_calls == 2:
                    self.handle.write(value[:10])
                    return 10
                return self.handle.write(value)

        def open_with_terminal_write_failure(path, *args, **kwargs):
            handle = original_open(path, *args, **kwargs)
            if path == report_path:
                return FailingWriteProxy(handle)
            return handle

        def simulated_completed_render(*args, **kwargs):
            self.output.write_bytes(b"completed render output")
            return {
                "status": "RENDERED",
                "output_path": str(self.output),
                "upload_performed": False,
                "publishing_enabled": False,
            }

        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "2", "--end", "8",
            "--execute", "--confirm-rights",
            "--output", str(self.output), "--report", str(report_path),
        ]
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip",
            side_effect=simulated_completed_render,
        ), patch.object(Path, "open", new=open_with_terminal_write_failure):
            self.assertEqual(main(), 2)

        # A failed report write does not prove rendering failed. Preserve the
        # output and require manual inspection rather than destructive cleanup.
        self.assertEqual(self.output.read_bytes(), b"completed render output")
        with self.assertRaises(json.JSONDecodeError):
            json.loads(report_path.read_text(encoding="utf-8"))
        fallback_path = report_path.with_name(report_path.name + ".terminal-fallback.json")
        fallback = json.loads(fallback_path.read_text(encoding="utf-8"))
        self.assertEqual(fallback["status"], "RENDERED")
        self.assertFalse(fallback["upload_performed"])
        self.assertFalse(fallback["publishing_enabled"])

    def test_terminal_fallback_writes_valid_json_with_real_trailing_newline(self):
        report_path = self.root / "newline-report.json"
        report_text = json.dumps({"status": "RUNNING"}, indent=2) + "\n"
        fallback_path = _write_exclusive_terminal_fallback(report_path, report_text)
        persisted = fallback_path.read_text(encoding="utf-8")
        self.assertTrue(persisted.endswith("\n"))
        self.assertEqual(json.loads(persisted), {"status": "RUNNING"})

    def test_terminal_fallback_rejects_short_write(self):
        report_path = self.root / "short-write-report.json"
        original_open = Path.open

        class ShortWriteProxy:
            def __init__(self, handle):
                self.handle = handle

            def __enter__(self):
                self.handle.__enter__()
                return self

            def __exit__(self, *args):
                return self.handle.__exit__(*args)

            def __getattr__(self, name):
                return getattr(self.handle, name)

            def write(self, value):
                self.handle.write(value[:-1])
                return len(value) - 1

        def open_with_short_write(path, *args, **kwargs):
            handle = original_open(path, *args, **kwargs)
            if path == report_path.with_name(report_path.name + ".terminal-fallback.json"):
                return ShortWriteProxy(handle)
            return handle

        with patch.object(Path, "open", new=open_with_short_write):
            with self.assertRaisesRegex(OSError, "write was incomplete"):
                _write_exclusive_terminal_fallback(report_path, '{"status":"RENDERED"}\n')
        self.assertTrue(
            report_path.with_name(report_path.name + ".terminal-fallback.json").exists()
        )

    def test_terminal_fallback_rejects_output_path_alias(self):
        report_path = self.root / "alias-report.json"
        output_alias = self.root / (report_path.name + ".terminal-fallback.json")
        with self.assertRaisesRegex(OSError, "aliases the selected source or output"):
            _write_exclusive_terminal_fallback(
                report_path, '{"status":"RENDERED"}\n', (self.source, output_alias)
            )
        self.assertFalse(output_alias.exists())

    def test_cli_partial_terminal_write_does_not_overwrite_existing_fallback(self):
        report_path = self.root / "fallback-collision.json"
        fallback_path = report_path.with_name(report_path.name + ".terminal-fallback.json")
        fallback_path.write_text("operator-owned sentinel", encoding="utf-8")
        original_open = Path.open

        class FailingWriteProxy:
            def __init__(self, handle):
                self.handle = handle
                self.write_calls = 0

            def __enter__(self):
                self.handle.__enter__()
                return self

            def __exit__(self, *args):
                return self.handle.__exit__(*args)

            def __getattr__(self, name):
                return getattr(self.handle, name)

            def write(self, value):
                self.write_calls += 1
                if self.write_calls == 3:
                    self.handle.write(value[:8])
                    raise OSError("simulated partial terminal report write")
                return self.handle.write(value)

        def open_with_failure(path, *args, **kwargs):
            handle = original_open(path, *args, **kwargs)
            if path == report_path:
                return FailingWriteProxy(handle)
            return handle

        def simulated_completed_render(*args, **kwargs):
            self.output.write_bytes(b"completed render output")
            return {
                "status": "RENDERED",
                "output_path": str(self.output),
                "upload_performed": False,
                "publishing_enabled": False,
            }

        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "2", "--end", "8",
            "--execute", "--confirm-rights",
            "--output", str(self.output), "--report", str(report_path),
        ]
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip",
            side_effect=simulated_completed_render,
        ), patch.object(Path, "open", new=open_with_failure):
            self.assertEqual(main(), 2)

        self.assertEqual(fallback_path.read_text(encoding="utf-8"), "operator-owned sentinel")
        self.assertEqual(self.output.read_bytes(), b"completed render output")

    def test_cli_terminal_fallback_uses_expanded_report_path(self):
        raw_report_path = Path("~/aro-terminal-report.json")
        expanded_report_path = self.root / "aro-terminal-report.json"
        fallback_path = self.root / "aro-terminal-report.json.terminal-fallback.json"
        original_expanduser = Path.expanduser
        original_open = Path.open

        def expanduser(path):
            if path == raw_report_path:
                return expanded_report_path
            return original_expanduser(path)

        class TerminalWriteFailure:
            def __init__(self, handle):
                self.handle = handle
                self.write_calls = 0

            def __enter__(self):
                self.handle.__enter__()
                return self

            def __exit__(self, *args):
                return self.handle.__exit__(*args)

            def __getattr__(self, name):
                return getattr(self.handle, name)

            def write(self, value):
                self.write_calls += 1
                if self.write_calls == 2:
                    self.handle.write(value[:8])
                    return 8
                return self.handle.write(value)

        def open_with_terminal_failure(path, *args, **kwargs):
            handle = original_open(path, *args, **kwargs)
            if path == expanded_report_path:
                return TerminalWriteFailure(handle)
            return handle

        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "2", "--end", "8",
            "--output", str(self.output), "--report", str(raw_report_path),
        ]
        with patch("sys.argv", argv), patch.object(Path, "expanduser", new=expanduser), patch.object(
            Path, "open", new=open_with_terminal_failure
        ), patch(
            "backend.app.single_clip_render.render_selected_clip",
            return_value={"status": "PLANNED", "upload_performed": False, "publishing_enabled": False},
        ), patch(
            "backend.app.single_clip_render._write_exclusive_terminal_fallback",
            return_value=fallback_path,
        ) as write_fallback:
            self.assertEqual(main(), 2)

        write_fallback.assert_called_once()
        self.assertEqual(write_fallback.call_args.args[0], expanded_report_path)

    def test_cli_terminal_failure_marks_snapshot_digest_unverified(self):
        report_path = self.root / "terminal-snapshot-failure.json"
        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "2", "--end", "8",
            "--execute", "--confirm-rights",
            "--report", str(report_path),
        ]
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip",
            side_effect=RuntimeError("snapshot failed"),
        ):
            self.assertEqual(main(), 1)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["source_snapshot_verified"])
        self.assertFalse(report["source_snapshot_created"])
        self.assertIsNone(report["source_sha256"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])

    def test_snapshot_cleanup_failure_preserves_verified_snapshot_and_render_state(self):
        temporary_snapshot_dir = self.root / "mock-snapshot-directory"
        temporary_snapshot_dir.mkdir()

        class CleanupFailure:
            def __enter__(self):
                return str(temporary_snapshot_dir)

            def __exit__(self, exc_type, exc_value, traceback):
                raise OSError("simulated temporary snapshot cleanup failure")

        rendered = {
            "status": "RENDERED",
            "processing_started": True,
            "source_preflight": PASS,
            "rendered_preflight": PASS,
            "rendered_duration_seconds": 6.0,
            "output_sha256": "c" * 64,
            "output_size_bytes": 987,
            "output_identity_verified": True,
            "upload_performed": False,
            "publishing_enabled": False,
        }
        with patch(
            "backend.app.single_clip_render.tempfile.TemporaryDirectory",
            return_value=CleanupFailure(),
        ), patch(
            "backend.app.single_clip_render._create_stable_source_snapshot",
            return_value="b" * 64,
        ), patch(
            "backend.app.single_clip_render._render_selected_clip_from_snapshot",
            return_value=rendered,
        ):
            report = render_selected_clip(
                self.source, self.output, 2, 8,
                execute=True, rights_confirmed=True,
            )

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(report["source_snapshot_created"])
        self.assertTrue(report["source_snapshot_verified"])
        self.assertEqual(report["source_sha256"], "b" * 64)
        self.assertEqual(report["processing_started"], True)
        self.assertEqual(report["render_status_before_cleanup_failure"], "RENDERED")
        self.assertEqual(report["source_preflight"], PASS)
        self.assertEqual(report["rendered_preflight"], PASS)
        self.assertEqual(report["rendered_duration_seconds"], 6.0)
        self.assertEqual(report["output_sha256"], "c" * 64)
        self.assertEqual(report["output_size_bytes"], 987)
        self.assertTrue(report["output_identity_verified"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        self.assertIn("temporary snapshot cleanup failed", report["error"])

    @patch(
        "backend.app.single_clip_render.sha256_selected_source",
        return_value="0" * 64,
    )
    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_candidate_dry_run_rechecks_trusted_digest_after_preflight(self, preflight, source_hash):
        expected = "a" * 64
        report = render_selected_clip(
            self.source, self.output, 2, 8,
            execute=False,
            expected_source_sha256=expected,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("no longer matches the trusted candidate inventory", report["error"])
        source_hash.assert_called_once_with(Path(self.source))
        self.assertFalse(self.output.exists())

    @patch(
        "backend.app.single_clip_render.sha256_selected_source",
        return_value=hashlib.sha256(b"synthetic video").hexdigest(),
    )
    @patch("backend.app.single_clip_render.inspect_one_video", return_value=PASS)
    def test_candidate_dry_run_records_verified_source_digest(self, preflight, source_hash):
        expected = hashlib.sha256(b"synthetic video").hexdigest()
        report = render_selected_clip(
            self.source, self.output, 2, 8,
            execute=False,
            expected_source_sha256=expected,
        )
        self.assertEqual(report["status"], "PLANNED")
        self.assertEqual(report["source_sha256"], expected)
        self.assertEqual(report["expected_source_sha256"], expected)
        source_hash.assert_called_once_with(Path(self.source))

    def test_render_exception_does_not_claim_processing_started(self, render, preflight):
        report = render_selected_clip(
            self.source, self.output, 2, 8,
            execute=True, rights_confirmed=True,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIsNone(report["processing_started"])
        self.assertTrue(report["source_snapshot_created"])
        self.assertTrue(report["source_snapshot_verified"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        render.assert_called_once()
        self.assertEqual(preflight.call_count, 1)

    def test_render_failure_after_snapshot_preserves_verified_snapshot_evidence(self):
        with patch(
            "backend.app.single_clip_render._create_stable_source_snapshot",
            return_value="a" * 64,
        ), patch(
            "backend.app.single_clip_render._render_selected_clip_from_snapshot",
            side_effect=RuntimeError("simulated FFmpeg failure"),
        ):
            report = render_selected_clip(
                self.source, self.output, 2, 8,
                execute=True, rights_confirmed=True,
            )
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(report["source_snapshot_verified"])
        self.assertTrue(report["source_snapshot_created"])
        self.assertEqual(report["source_sha256"], "a" * 64)
        self.assertIsNone(report["processing_started"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])

    def test_cli_json_reports_escape_surrogate_filesystem_names(self):
        report_path = self.root / "surrogate-path-report.json"
        source_with_surrogate = str(self.root / ("selected-" + chr(0xDCFF) + ".mp4"))
        argv = [
            "single_clip_render.py", source_with_surrogate,
            "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]
        planned = {
            "status": "PLANNED",
            "upload_performed": False,
            "publishing_enabled": False,
            "message": "dry-run only",
        }
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip",
            return_value=planned,
        ), redirect_stdout(io.StringIO()):
            self.assertEqual(main(), 0)

        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PLANNED")
        self.assertEqual(report["source_path"], source_with_surrogate)
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])

    def test_cli_reports_execution_request_without_rights_confirmation(self):
        report_path = self.root / "blocked-report.json"
        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
            "--execute",
        ]
        blocked = {
            "status": "BLOCKED",
            "upload_performed": False,
            "publishing_enabled": False,
            "error": "render execution requires --confirm-rights",
        }
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip",
            return_value=blocked,
        ):
            self.assertEqual(main(), 1)

        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "BLOCKED")
        self.assertTrue(report["execution_requested"])
        self.assertFalse(report["rights_confirmation_supplied"])
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])

    def test_cli_records_terminal_render_failure_in_reserved_report(self):
        report_path = self.root / "failed-report.json"
        with patch("sys.argv", [
            "single_clip_render", str(self.source), "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
            "--execute", "--confirm-rights",
        ]):
            with patch(
                "backend.app.single_clip_render.render_selected_clip",
                side_effect=RuntimeError("simulated render failure"),
            ):
                self.assertEqual(main(), 1)

        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(report["execution_requested"])
        self.assertEqual(report["error"], "simulated render failure")
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])
        self.assertIn("inspect any output file", report["message"])
        self.assertFalse(self.output.exists())


    def test_candidate_csv_rejects_invalid_path_types_before_path_conversion(self):
        for invalid_path in (None, 7, [], {}):
            with self.subTest(invalid_path=type(invalid_path).__name__):
                with self.assertRaisesRegex(
                    ValueError, "candidate CSV path must be a non-empty string or pathlib.Path"
                ):
                    load_selected_candidate(invalid_path, 1)

    def test_candidate_csv_rejects_blank_path_strings(self):
        for invalid_path in ("", "   ", "\t"):
            with self.subTest(invalid_path=repr(invalid_path)):
                with self.assertRaisesRegex(
                    ValueError, "candidate CSV path must be a non-empty string or pathlib.Path"
                ):
                    load_selected_candidate(invalid_path, 1)

    def test_candidate_csv_rejects_invalid_utf8_as_validation_error(self):
        pack = self.root / "invalid-utf8-candidates.csv"
        pack.write_bytes(b"source_id,start_seconds,end_seconds,duration_seconds,renderable\n\xff,2,8,6,True\n")
        with self.assertRaisesRegex(ValueError, "candidate CSV could not be read"):
            load_selected_candidate(pack, 1)

    def test_candidate_csv_accepts_utf8_bom_from_spreadsheet_export(self):
        pack = self.root / "bom-candidates.csv"
        pack.write_text(
            "\ufeffsource_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,2,8,6,True\n",
            encoding="utf-8",
        )
        selected = load_selected_candidate(pack, 1)
        self.assertEqual(selected["source_id"], "authorized-demo")

    def test_candidate_csv_rejects_duplicate_required_headers(self):
        pack = self.root / "duplicate-headers.csv"
        pack.write_text(
            "source_id,source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "one,two,2,8,6,True\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "duplicate column names"):
            load_selected_candidate(pack, 1)

    def test_candidate_csv_rejects_blank_header_cells(self):
        pack = self.root / "blank-header.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable,\n"
            "authorized-demo,2,8,6,True,unexpected\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "blank or duplicate column names"):
            load_selected_candidate(pack, 1)

    def test_candidate_csv_rejects_selected_row_with_extra_values(self):
        pack = self.root / "extra-values.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,2,8,6,True,unexpected\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "more values than its header"):
            load_selected_candidate(pack, 1)

    def test_candidate_csv_rejects_selected_row_missing_required_value(self):
        pack = self.root / "missing-value.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,2,8,,True\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "missing required values"):
            load_selected_candidate(pack, 1)


    def test_cli_terminal_fallback_persists_file_at_expanded_report_path(self):
        report_argument = Path("~/expanded-terminal-report.json")
        expanded_report = self.root / "expanded-terminal-report.json"
        original_expanduser = Path.expanduser
        original_open = Path.open

        def expand_selected_report(path):
            if path == report_argument:
                return expanded_report
            return original_expanduser(path)

        class FailingWriteProxy:
            def __init__(self, handle):
                self.handle = handle
                self.write_calls = 0

            def __enter__(self):
                self.handle.__enter__()
                return self

            def __exit__(self, *args):
                return self.handle.__exit__(*args)

            def __getattr__(self, name):
                return getattr(self.handle, name)

            def write(self, value):
                self.write_calls += 1
                if self.write_calls == 2:
                    self.handle.write(value[:10])
                    return 10
                return self.handle.write(value)

        def open_with_terminal_write_failure(path, *args, **kwargs):
            handle = original_open(path, *args, **kwargs)
            if path == expanded_report:
                return FailingWriteProxy(handle)
            return handle

        def simulated_completed_render(*args, **kwargs):
            self.output.write_bytes(b"completed render output")
            return {
                "status": "RENDERED",
                "output_path": str(self.output),
                "upload_performed": False,
                "publishing_enabled": False,
            }

        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "2", "--end", "8",
            "--execute", "--confirm-rights",
            "--output", str(self.output), "--report", str(report_argument),
        ]
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip",
            side_effect=simulated_completed_render,
        ), patch.object(Path, "expanduser", new=expand_selected_report), patch.object(
            Path, "open", new=open_with_terminal_write_failure
        ):
            self.assertEqual(main(), 2)

        self.assertEqual(self.output.read_bytes(), b"completed render output")
        fallback_path = expanded_report.with_name(
            expanded_report.name + ".terminal-fallback.json"
        )
        self.assertTrue(fallback_path.exists())
        fallback = json.loads(fallback_path.read_text(encoding="utf-8"))
        self.assertEqual(fallback["status"], "RENDERED")
        self.assertFalse(fallback["upload_performed"])
        self.assertFalse(fallback["publishing_enabled"])


    def test_cli_preserves_valid_running_report_when_terminal_metadata_is_non_finite(self):
        report_path = self.root / "non-finite-terminal-report.json"
        planned_with_invalid_metadata = {
            "status": "PLANNED",
            "upload_performed": False,
            "publishing_enabled": False,
            "unexpected_metric": float("nan"),
        }
        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip",
            return_value=planned_with_invalid_metadata,
        ):
            self.assertEqual(main(), 2)

        report_text = report_path.read_text(encoding="utf-8")
        report = json.loads(report_text)
        self.assertEqual(report["status"], "RUNNING")
        self.assertNotIn("NaN", report_text)
        self.assertFalse(self.output.exists())


    def test_cli_fallback_resolution_error_keeps_output_inspection_warning(self):
        report_path = self.root / "fallback-resolution-error.json"
        fallback_path = report_path.with_name(
            report_path.name + ".terminal-fallback.json"
        )
        original_open = Path.open
        original_resolve = Path.resolve

        class TerminalWriteFailure:
            def __init__(self, handle):
                self.handle = handle
                self.write_calls = 0

            def __enter__(self):
                self.handle.__enter__()
                return self

            def __exit__(self, *args):
                return self.handle.__exit__(*args)

            def __getattr__(self, name):
                return getattr(self.handle, name)

            def write(self, value):
                self.write_calls += 1
                if self.write_calls == 2:
                    self.handle.write(value[:8])
                    return 8
                return self.handle.write(value)

        def open_with_terminal_failure(path, *args, **kwargs):
            handle = original_open(path, *args, **kwargs)
            if path == report_path:
                return TerminalWriteFailure(handle)
            return handle

        def resolve_with_fallback_error(path, *args, **kwargs):
            if path == fallback_path:
                raise RuntimeError("simulated symlink loop")
            return original_resolve(path, *args, **kwargs)

        def simulated_completed_render(*args, **kwargs):
            self.output.write_bytes(b"completed render output")
            return {
                "status": "RENDERED",
                "output_path": str(self.output),
                "upload_performed": False,
                "publishing_enabled": False,
            }

        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "2", "--end", "8",
            "--execute", "--confirm-rights",
            "--output", str(self.output), "--report", str(report_path),
        ]
        stderr = io.StringIO()
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip",
            side_effect=simulated_completed_render,
        ), patch.object(Path, "open", new=open_with_terminal_failure), patch.object(
            Path, "resolve", new=resolve_with_fallback_error
        ), redirect_stderr(stderr):
            self.assertEqual(main(), 2)

        self.assertEqual(self.output.read_bytes(), b"completed render output")
        self.assertFalse(fallback_path.exists())
        self.assertIn("fallback creation also failed", stderr.getvalue())
        self.assertIn("Inspect any output file manually before retrying", stderr.getvalue())


    def test_candidate_csv_rejects_malformed_quoting_even_after_selected_row(self):
        pack = self.root / "malformed-quoting.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,1,5,4,True\n"
            '"unterminated,2,6,4,True\n',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "candidate CSV could not be read"):
            load_selected_candidate(pack, 1)

    def test_candidate_csv_rejects_extra_cells_in_any_row(self):
        pack = self.root / "extra-cells.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,1,5,4,True,unexpected\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "more values than its header"):
            load_selected_candidate(pack, 1)

    def test_candidate_csv_rejects_missing_cells_in_any_row(self):
        pack = self.root / "missing-cells.csv"
        pack.write_text(
            "source_id,start_seconds,end_seconds,duration_seconds,renderable\n"
            "authorized-demo,1,5,4\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "missing required values"):
            load_selected_candidate(pack, 1)


    def test_snapshot_path_resolution_symlink_loop_is_normalized(self):
        snapshot = self.root / "snapshot-resolution-loop.mp4"
        with patch.object(Path, "resolve", side_effect=RuntimeError("simulated symlink loop")):
            with self.assertRaisesRegex(ValueError, "source or snapshot path could not be resolved"):
                _create_stable_source_snapshot(self.source, snapshot)
        self.assertEqual(self.source.read_bytes(), b"synthetic video")
        self.assertFalse(snapshot.exists())


    def test_cli_marks_output_inspection_required_when_renderer_raises_after_output_creation(self):
        report_path = self.root / "render-exception-report.json"

        def create_possible_output_then_raise(*args, **kwargs):
            self.output.write_bytes(b"possible completed output")
            raise OSError("simulated post-output renderer exception")

        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "2", "--end", "8",
            "--execute", "--confirm-rights",
            "--output", str(self.output), "--report", str(report_path),
        ]
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render.render_selected_clip",
            side_effect=create_possible_output_then_raise,
        ):
            self.assertEqual(main(), 1)

        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(report["output_inspection_required"])
        self.assertEqual(report["output_path"], str(self.output))
        self.assertEqual(self.output.read_bytes(), b"possible completed output")
        self.assertFalse(report["upload_performed"])
        self.assertFalse(report["publishing_enabled"])


    def test_terminal_fallback_path_is_reported_when_directory_sync_fails(self):
        report_path = self.root / "directory-sync-failure.json"
        report_text = json.dumps({"status": "FAIL"}) + "\n"
        stderr = io.StringIO()

        with patch(
            "backend.app.single_clip_render._fsync_parent_directory",
            side_effect=OSError("simulated directory fsync failure"),
        ), redirect_stderr(stderr):
            fallback_path = _write_exclusive_terminal_fallback(
                report_path, report_text, (self.source, self.output)
            )

        self.assertTrue(fallback_path.is_file())
        self.assertEqual(fallback_path.read_text(encoding="utf-8"), report_text)
        self.assertIn(str(fallback_path), stderr.getvalue())
        self.assertIn("parent-directory synchronization failed", stderr.getvalue())
        self.assertIn("Inspect this report and any rendered output before retrying", stderr.getvalue())


    def test_partial_terminal_fallback_write_reports_preserved_sidecar_path(self):
        report_path = self.root / "partial-fallback.json"
        fallback_path = report_path.with_name(
            report_path.name + ".terminal-fallback.json"
        )
        report_text = json.dumps({"status": "FAIL", "message": "complete"}) + "\n"
        original_open = Path.open

        class PartialWrite:
            def __init__(self, handle):
                self.handle = handle

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                self.handle.close()

            def write(self, value):
                prefix = value[:7]
                self.handle.write(prefix)
                return len(prefix)

            def flush(self):
                return self.handle.flush()

            def fileno(self):
                return self.handle.fileno()

        def open_with_partial_fallback(path, *args, **kwargs):
            handle = original_open(path, *args, **kwargs)
            if path == fallback_path:
                return PartialWrite(handle)
            return handle

        with patch.object(Path, "open", new=open_with_partial_fallback):
            with self.assertRaisesRegex(OSError, str(fallback_path)):
                _write_exclusive_terminal_fallback(
                    report_path, report_text, (self.source, self.output)
                )

        self.assertTrue(fallback_path.is_file())
        self.assertEqual(fallback_path.read_text(encoding="utf-8"), report_text[:7])


    def test_report_handle_identity_check_detects_actual_path_replacement(self):
        report_path = self.root / "reserved-report.json"
        displaced_path = self.root / "displaced-report.json"
        report_path.write_text("reserved", encoding="utf-8")
        with report_path.open("r+", encoding="utf-8") as handle:
            self.assertTrue(_report_handle_matches_path(handle, report_path))
            report_path.replace(displaced_path)
            report_path.write_text("replacement", encoding="utf-8")
            self.assertFalse(_report_handle_matches_path(handle, report_path))
        self.assertEqual(displaced_path.read_text(encoding="utf-8"), "reserved")
        self.assertEqual(report_path.read_text(encoding="utf-8"), "replacement")


    def test_cli_stops_before_media_when_report_path_identity_check_fails(self):
        report_path = self.root / "replaced-before-media.json"
        fallback_path = report_path.with_name(report_path.name + ".terminal-fallback.json")
        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render._report_handle_matches_path",
            return_value=False,
        ), patch(
            "backend.app.single_clip_render.render_selected_clip"
        ) as render, redirect_stderr(io.StringIO()):
            self.assertEqual(main(), 2)

        render.assert_not_called()
        self.assertTrue(fallback_path.is_file())
        fallback = json.loads(fallback_path.read_text(encoding="utf-8"))
        self.assertEqual(fallback["status"], "RUNNING")
        self.assertFalse(fallback["upload_performed"])
        self.assertFalse(fallback["publishing_enabled"])

    def test_cli_falls_back_when_report_path_identity_changes_during_terminal_write(self):
        report_path = self.root / "replaced-during-terminal-write.json"
        fallback_path = report_path.with_name(report_path.name + ".terminal-fallback.json")
        argv = [
            "single_clip_render.py", str(self.source),
            "--start", "1", "--end", "5",
            "--output", str(self.output), "--report", str(report_path),
        ]
        planned = {
            "status": "PLANNED",
            "upload_performed": False,
            "publishing_enabled": False,
        }
        # Initial reservation check and pre-write check pass; post-write check
        # detects that the pathname no longer identifies the reserved inode.
        with patch("sys.argv", argv), patch(
            "backend.app.single_clip_render._report_handle_matches_path",
            side_effect=[True, True, False],
        ), patch(
            "backend.app.single_clip_render.render_selected_clip",
            return_value=planned,
        ), redirect_stderr(io.StringIO()):
            self.assertEqual(main(), 2)

        self.assertTrue(fallback_path.is_file())
        fallback = json.loads(fallback_path.read_text(encoding="utf-8"))
        self.assertEqual(fallback["status"], "PLANNED")
        self.assertFalse(fallback["upload_performed"])
        self.assertFalse(fallback["publishing_enabled"])


if __name__ == "__main__":
    unittest.main()
