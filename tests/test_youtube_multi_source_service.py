"""Tests for optional bounded multi-source stream lifecycle."""
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

from backend.app.consent_registry import ConsentRegistry
from backend.app.models import PermissionRecord
from backend.app.youtube_multi_source_service import MultiSourceStreamService


class MultiSourceServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.registry = ConsentRegistry(Path(self.temp.name) / "consent.sqlite3")
        now = datetime.now(timezone.utc)
        for video in ("v1", "v2", "v3"):
            self.registry.grant(PermissionRecord(
                source_id=video, granted_by="creator",
                scopes=frozenset({"analyze_chat"}),
                granted_at=now - timedelta(minutes=1),
            ))

    def tearDown(self):
        self.temp.cleanup()

    def service(self, limit=2):
        return MultiSourceStreamService(registry=self.registry,
                                        max_concurrent_sources=limit)

    def test_service_is_inert_until_explicit_start(self):
        service = self.service()
        self.assertEqual(service.status(), ())
        self.assertEqual(service.shutdown(), ())

    def test_enforces_concurrency_limit_and_individual_stop(self):
        service = self.service(limit=1)
        gate = threading.Event()
        entered = threading.Event()

        def stream_factory(_chat, _cursor):
            entered.set()
            gate.wait(2)
            return iter(())

        service.start_source(video_id="v1", live_chat_id="c1",
            stream_factory=stream_factory, on_response=lambda _: None,
            max_responses=1, max_runtime_seconds=5)
        self.assertTrue(entered.wait(1))
        with self.assertRaises(RuntimeError):
            service.start_source(video_id="v2", live_chat_id="c2",
                stream_factory=lambda *_: iter(()), on_response=lambda _: None,
                max_responses=1, max_runtime_seconds=5)
        self.assertTrue(service.stop_source("v1", join_timeout=0.01))
        gate.set()
        deadline = time.monotonic() + 2
        while not service.status("v1")[0].finished and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(service.status("v1")[0].finished)

    def test_rejects_duplicate_running_source(self):
        service = self.service()
        gate = threading.Event()
        entered = threading.Event()
        def factory(*_):
            entered.set()
            gate.wait(2)
            return iter(())
        service.start_source(video_id="v1", live_chat_id="c1",
            stream_factory=factory, on_response=lambda _: None,
            max_responses=1, max_runtime_seconds=5)
        self.assertTrue(entered.wait(1))
        with self.assertRaises(ValueError):
            service.start_source(video_id="v1", live_chat_id="c1",
                stream_factory=lambda *_: iter(()), on_response=lambda _: None,
                max_responses=1, max_runtime_seconds=5)
        gate.set()
        service.shutdown(join_timeout=1)

    def test_captures_permission_failure_in_health_status(self):
        service = self.service()
        self.registry.revoke("v1", actor="owner")
        service.start_source(video_id="v1", live_chat_id="c1",
            stream_factory=Mock(), on_response=lambda _: None,
            max_responses=1, max_runtime_seconds=5)
        deadline = time.monotonic() + 2
        while not service.status("v1")[0].finished and time.monotonic() < deadline:
            time.sleep(0.01)
        status = service.status("v1")[0]
        self.assertEqual(status.state, "failed")
        self.assertIn("PermissionError", status.error)

    def test_shutdown_stops_all_workers(self):
        service = self.service(limit=2)
        gates = [threading.Event(), threading.Event()]
        entered = [threading.Event(), threading.Event()]
        for index, video in enumerate(("v1", "v2")):
            def factory(_chat, _cursor, i=index):
                entered[i].set()
                gates[i].wait(2)
                return iter(())
            service.start_source(video_id=video, live_chat_id=f"c{index}",
                stream_factory=factory, on_response=lambda _: None,
                max_responses=1, max_runtime_seconds=5)
        self.assertTrue(all(event.wait(1) for event in entered))
        pending = service.shutdown(join_timeout=0.01)
        self.assertEqual(set(pending), {"v1", "v2"})
        for gate in gates:
            gate.set()
        deadline = time.monotonic() + 2
        while service.status() and any(not s.finished for s in service.status()) and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(all(s.finished for s in service.status()))

    def test_rejects_invalid_concurrency(self):
        with self.assertRaises(ValueError):
            self.service(limit=0)


if __name__ == "__main__":
    unittest.main()
