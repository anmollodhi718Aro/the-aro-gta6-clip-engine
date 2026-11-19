"""Integration tests for polling worker checkpoint resume semantics."""
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

from backend.app.consent_registry import ConsentRegistry
from backend.app.models import ChatEvent, PermissionRecord
from backend.app.polling_checkpoint_store import PollingCheckpointStore
from backend.app.youtube_live_chat import YouTubeChatBatch
from backend.app.youtube_polling_worker import run_bounded_polling


class PollingCheckpointIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.registry = ConsentRegistry(root / "consent.sqlite3")
        self.checkpoints = PollingCheckpointStore(root / "polling.sqlite3")
        now = datetime.now(timezone.utc)
        self.registry.grant(PermissionRecord(
            source_id="video-1", granted_by="creator",
            scopes=frozenset({"analyze_chat"}),
            granted_at=now - timedelta(minutes=1)))

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def batch(token):
        now = datetime.now(timezone.utc)
        return YouTubeChatBatch("video-1", "chat-1",
            (ChatEvent("event-" + (token or "final"), "video-1", now, "hello"),),
            token, 1000, False)

    def test_worker_resumes_saved_live_chat_and_page_token(self):
        self.checkpoints.save("video-1", live_chat_id="chat-1", page_token="resume-here")
        client = Mock()
        client.fetch_recent_messages.return_value = self.batch("next-page")
        run_bounded_polling(client=client, registry=self.registry, video_id="video-1",
            on_batch=lambda _: None, stop_event=threading.Event(), max_batches=1,
            max_runtime_seconds=10, checkpoint_store=self.checkpoints)
        kwargs = client.fetch_recent_messages.call_args.kwargs
        self.assertEqual(kwargs["live_chat_id"], "chat-1")
        self.assertEqual(kwargs["page_token"], "resume-here")
        self.assertEqual(self.checkpoints.load("video-1").page_token, "next-page")

    def test_callback_failure_does_not_advance_checkpoint(self):
        self.checkpoints.save("video-1", live_chat_id="chat-1", page_token="old-page")
        client = Mock()
        client.fetch_recent_messages.return_value = self.batch("new-page")
        def fail(_batch):
            raise RuntimeError("durable ingestion failed")
        with self.assertRaises(RuntimeError):
            run_bounded_polling(client=client, registry=self.registry, video_id="video-1",
                on_batch=fail, stop_event=threading.Event(), max_batches=1,
                max_runtime_seconds=10, checkpoint_store=self.checkpoints)
        self.assertEqual(self.checkpoints.load("video-1").page_token, "old-page")

if __name__ == "__main__":
    unittest.main()
