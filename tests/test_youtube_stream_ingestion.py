"""Tests for durable streamList response ingestion glue."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from backend.app.chat_event_store import ChatEventStore
from backend.app.youtube_stream_ingestion import make_durable_response_handler

class DurableStreamIngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=ChatEventStore(Path(self.temp.name)/"events.sqlite3")
    def tearDown(self): self.temp.cleanup()
    def response(self, event_id="evt-1", text="hello"):
        snippet=SimpleNamespace(published_at="2026-11-18T10:00:00Z",display_message=text)
        return SimpleNamespace(items=[SimpleNamespace(id=event_id,snippet=snippet)])
    def test_persists_converted_events(self):
        handler=make_durable_response_handler(video_id="video-1",event_store=self.store)
        handler(self.response())
        events=self.store.list_events("video-1")
        self.assertEqual(len(events),1)
        self.assertEqual(events[0].text,"hello")
    def test_replayed_response_is_idempotent(self):
        handler=make_durable_response_handler(video_id="video-1",event_store=self.store)
        handler(self.response()); handler(self.response())
        self.assertEqual(len(self.store.list_events("video-1")),1)
    def test_conflicting_replay_fails_closed(self):
        handler=make_durable_response_handler(video_id="video-1",event_store=self.store)
        handler(self.response())
        with self.assertRaises(ValueError): handler(self.response(text="changed"))
        self.assertEqual(len(self.store.list_events("video-1")),1)
    def test_rejects_blank_video_id(self):
        with self.assertRaises(ValueError):
            make_durable_response_handler(video_id=" ",event_store=self.store)

if __name__ == "__main__": unittest.main()
