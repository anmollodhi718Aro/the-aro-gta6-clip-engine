"""Tests for the single-page scheduler-to-ingestion orchestrator."""
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

from backend.app.chat_event_store import ChatEventStore
from backend.app.consent_registry import ConsentRegistry
from backend.app.models import ChatEvent, PermissionRecord
from backend.app.polling_checkpoint_store import PollingCheckpointStore
from backend.app.quota_scheduler import QuotaAwareScheduler
from backend.app.scheduled_ingestion import poll_one_due_source
from backend.app.youtube_live_chat import YouTubeChatBatch


class ScheduledIngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.scheduler = QuotaAwareScheduler(root / "scheduler.sqlite3")
        self.registry = ConsentRegistry(root / "consent.sqlite3")
        self.checkpoints = PollingCheckpointStore(root / "cursor.sqlite3")
        self.events = ChatEventStore(root / "events.sqlite3")
        self.client = Mock()
        self.now = datetime.now(timezone.utc)
        self.registry.grant(PermissionRecord(
            source_id="video-1", granted_by="creator",
            scopes=frozenset({"analyze_chat"}),
            granted_at=self.now - timedelta(minutes=1)))
        self.scheduler.configure_source("video-1", interval_seconds=10,
            request_cost_units=5, now=self.now)

    def tearDown(self):
        self.temp.cleanup()

    def test_one_page_fetch_persists_events_then_cursor(self):
        event = ChatEvent("event-1", "video-1", self.now, "hello")
        self.client.fetch_recent_messages.return_value = YouTubeChatBatch(
            "video-1", "chat-1", (event,), "next-token", 1000, False)
        result = poll_one_due_source(scheduler=self.scheduler, registry=self.registry,
            client=self.client, checkpoints=self.checkpoints, events=self.events,
            daily_quota_units=100, now=self.now)
        self.assertEqual(result.reservation.source_id, "video-1")
        self.assertEqual(result.ingestion.inserted, 1)
        self.assertEqual(self.checkpoints.load("video-1").page_token, "next-token")
        self.assertEqual(self.events.list_events("video-1"), [event])

    def test_resume_uses_saved_cursor_and_repeat_is_deduplicated(self):
        self.checkpoints.save("video-1", live_chat_id="chat-1", page_token="resume-token")
        self.client.fetch_recent_messages.return_value = YouTubeChatBatch(
            "video-1", "chat-1", (), None, 1000, False)
        poll_one_due_source(scheduler=self.scheduler, registry=self.registry,
            client=self.client, checkpoints=self.checkpoints, events=self.events,
            daily_quota_units=100, now=self.now)
        kwargs = self.client.fetch_recent_messages.call_args.kwargs
        self.assertEqual(kwargs["live_chat_id"], "chat-1")
        self.assertEqual(kwargs["page_token"], "resume-token")

    def test_revoked_consent_blocks_fetch(self):
        self.registry.revoke("video-1", actor="creator")
        with self.assertRaises(PermissionError):
            poll_one_due_source(scheduler=self.scheduler, registry=self.registry,
                client=self.client, checkpoints=self.checkpoints, events=self.events,
                daily_quota_units=100, now=self.now)
        self.client.fetch_recent_messages.assert_not_called()

if __name__ == "__main__":
    unittest.main()
