"""Tests for durable YouTube polling checkpoints."""
import tempfile
import unittest
from pathlib import Path

from backend.app.polling_checkpoint_store import PollingCheckpointStore


class PollingCheckpointStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "polling.sqlite3"
        self.store = PollingCheckpointStore(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_round_trip_survives_new_store_instance(self):
        saved = self.store.save("video-1", live_chat_id="chat-1", page_token="page-2")
        restored = PollingCheckpointStore(self.path).load("video-1")
        self.assertEqual(restored.video_id, "video-1")
        self.assertEqual(restored.live_chat_id, "chat-1")
        self.assertEqual(restored.page_token, "page-2")
        self.assertEqual(restored.updated_at, saved.updated_at)

    def test_save_can_clear_page_token_after_successful_final_page(self):
        self.store.save("video-1", live_chat_id="chat-1", page_token="page-2")
        saved = self.store.save("video-1", live_chat_id="chat-1", page_token=None)
        self.assertIsNone(saved.page_token)
        self.assertIsNone(self.store.load("video-1").page_token)

    def test_clear_is_idempotent(self):
        self.assertFalse(self.store.clear("video-1"))
        self.store.save("video-1", live_chat_id="chat-1", page_token="p2")
        self.assertTrue(self.store.clear("video-1"))
        self.assertFalse(self.store.clear("video-1"))
        self.assertIsNone(self.store.load("video-1"))

    def test_rejects_blank_identifiers_and_tokens(self):
        for bad in ("", "  "):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                self.store.load(bad)
        with self.assertRaises(ValueError):
            self.store.save("video-1", live_chat_id="chat-1", page_token=" ")

if __name__ == "__main__":
    unittest.main()
