"""Tests for bounded YouTube polling and consent re-checks."""
import tempfile, threading, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock
from backend.app.consent_registry import ConsentRegistry
from backend.app.models import ChatEvent, PermissionRecord
from backend.app.youtube_live_chat import YouTubeChatBatch
from backend.app.youtube_polling_worker import run_bounded_polling

class PollingWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.registry = ConsentRegistry(Path(self.temp.name) / "consent.sqlite3")
        now = datetime.now(timezone.utc)
        self.registry.grant(PermissionRecord(source_id="video-1", granted_by="creator",
            scopes=frozenset({"analyze_chat"}), granted_at=now - timedelta(minutes=1)))
    def tearDown(self): self.temp.cleanup()
    def batch(self, token="next", offline=False, interval=2500):
        now = datetime.now(timezone.utc)
        return YouTubeChatBatch("video-1", "chat-1",
            (ChatEvent("event-1", "video-1", now, "hello"),), token, interval, offline)
    def test_batch_limit_and_server_interval(self):
        client = Mock(); client.fetch_recent_messages.side_effect = [self.batch("p2"), self.batch(None)]
        received, waits = [], []
        result = run_bounded_polling(client=client, registry=self.registry, video_id="video-1",
            on_batch=received.append, stop_event=threading.Event(), max_batches=2,
            max_runtime_seconds=30, wait=lambda seconds: waits.append(seconds) or False)
        self.assertEqual((result.batches_fetched, result.events_received), (2, 2))
        self.assertEqual(waits, [2.5])
        self.assertEqual(client.fetch_recent_messages.call_args_list[1].kwargs["page_token"], "p2")
    def test_permission_is_rechecked_after_wait(self):
        client = Mock(); client.fetch_recent_messages.return_value = self.batch()
        def revoke(_seconds): self.registry.revoke("video-1", actor="owner"); return False
        with self.assertRaises(PermissionError):
            run_bounded_polling(client=client, registry=self.registry, video_id="video-1",
                on_batch=lambda batch: None, stop_event=threading.Event(), max_batches=3,
                max_runtime_seconds=30, wait=revoke)
        self.assertEqual(client.fetch_recent_messages.call_count, 1)
    def test_stops_when_chat_offline(self):
        client = Mock(); client.fetch_recent_messages.return_value = self.batch(offline=True)
        result = run_bounded_polling(client=client, registry=self.registry, video_id="video-1",
            on_batch=lambda batch: None, stop_event=threading.Event(), max_batches=5,
            max_runtime_seconds=30, wait=lambda _: False)
        self.assertEqual(result.batches_fetched, 1)
    def test_stop_event_prevents_fetch(self):
        stop = threading.Event(); stop.set(); client = Mock()
        result = run_bounded_polling(client=client, registry=self.registry, video_id="video-1",
            on_batch=lambda batch: None, stop_event=stop, max_batches=5, max_runtime_seconds=30)
        self.assertEqual(result.batches_fetched, 0); client.fetch_recent_messages.assert_not_called()
    def test_rejects_invalid_limits(self):
        client = Mock()
        for batches, duration in [(0, 5), (10001, 5), (1, float("inf")), (1, 0)]:
            with self.subTest(batches=batches, duration=duration), self.assertRaises(ValueError):
                run_bounded_polling(client=client, registry=self.registry, video_id="video-1",
                    on_batch=lambda batch: None, stop_event=threading.Event(),
                    max_batches=batches, max_runtime_seconds=duration)

if __name__ == "__main__": unittest.main()