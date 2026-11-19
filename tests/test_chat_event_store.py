"""Tests for durable, idempotent chat event storage."""
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.chat_event_store import ChatEventStore
from backend.app.models import ChatEvent


class ChatEventStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "events.sqlite3"
        self.store = ChatEventStore(self.path)
        self.event = ChatEvent("event-1", "video-1",
            datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc), "hello")

    def tearDown(self):
        self.temp.cleanup()

    def test_persists_across_instances_and_counts_duplicate(self):
        first = self.store.persist([self.event])
        second = ChatEventStore(self.path).persist([self.event])
        self.assertEqual((first.inserted, first.duplicates), (1, 0))
        self.assertEqual((second.inserted, second.duplicates), (0, 1))
        self.assertEqual(self.store.list_events("video-1"), [self.event])

    def test_conflicting_reuse_is_rejected_and_batch_rolls_back(self):
        self.store.persist([self.event])
        new_event = ChatEvent("event-2", "video-1", self.event.timestamp, "new")
        conflict = ChatEvent("event-1", "video-1", self.event.timestamp, "changed")
        with self.assertRaisesRegex(ValueError, "conflicting duplicate"):
            self.store.persist([new_event, conflict])
        # The pre-existing row remains, but the earlier event-2 insert rolls back.
        self.assertEqual(self.store.list_events("video-1"), [self.event])

    def test_same_event_id_on_different_source_is_independent(self):
        other = ChatEvent("event-1", "video-2", self.event.timestamp, "other source")
        self.assertEqual(self.store.persist([self.event, other]).inserted, 2)

    def test_timezone_equivalent_duplicate_is_idempotent(self):
        # Simulate a row written by the previous version before UTC normalization.
        with self.store._connect() as db:
            db.execute(
                "INSERT INTO chat_events (source_id, event_id, timestamp, text, ingested_at) "
                "VALUES (?, ?, ?, ?, ?)",
                ("video-1", "event-1", "2026-11-18T17:30:00+05:30", "hello",
                 "2026-11-18T12:00:00+00:00"),
            )
        result = self.store.persist([self.event])
        self.assertEqual((result.inserted, result.duplicates), (0, 1))
        stored = self.store.list_events(
            "video-1"
        )[0]
        self.assertEqual(stored.timestamp.utcoffset(), timedelta(0))

    def test_events_list_instant_order_for_legacy_timezone_offsets(self):
        # The later instant sorts first as text; parsed UTC ordering must win.
        with self.store._connect() as db:
            db.executemany(
                "INSERT INTO chat_events (source_id, event_id, timestamp, text, ingested_at) "
                "VALUES (?, ?, ?, ?, ?)",
                [
                    ("video-1", "event-later", "2026-11-18T07:30:00-05:00", "later",
                     "2026-11-19T00:00:00+00:00"),
                    ("video-1", "event-earlier", "2026-11-18T12:00:00+00:00", "earlier",
                     "2026-11-19T00:00:00+00:00"),
                ],
            )
        listed = self.store.list_events(
            "video-1"
        )
        self.assertEqual([event.event_id for event in listed], ["event-earlier", "event-later"])

    def test_batch_callback_helper(self):
        class Batch:
            events = (self.event,)
        result = self.store.persist_batch(Batch())
        self.assertEqual(result.inserted, 1)

if __name__ == "__main__":
    unittest.main()
