"""Tests for the read-only YouTube public live chat adapter."""

import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from backend.app.models import PermissionRecord
from backend.app.youtube_live_chat import YouTubeApiError, YouTubeLiveChatClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class YouTubeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.permission = PermissionRecord(
            source_id="video123",
            granted_by="creator",
            scopes=frozenset({"analyze_chat"}),
            granted_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self.client = YouTubeLiveChatClient(api_key="test-key")

    def test_requires_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                YouTubeLiveChatClient()

    def test_finds_active_live_chat_id(self):
        payload = {"items": [{"liveStreamingDetails": {"activeLiveChatId": "chat-abc"}}]}
        with patch("backend.app.youtube_live_chat.urlopen", return_value=FakeResponse(payload)):
            self.assertEqual(self.client.get_active_live_chat_id("video123"), "chat-abc")

    def test_maps_text_messages_to_minimal_events(self):
        payload = {
            "items": [
                {"id": "m1", "snippet": {"publishedAt": "2026-11-18T12:00:01Z", "displayMessage": "Hello"}},
                {"id": "m2", "snippet": {"publishedAt": "2026-11-18T12:00:02Z", "textMessageDetails": {"messageText": "GTA"}}},
                {"id": "m3", "snippet": {"publishedAt": "2026-11-18T12:00:03Z", "type": "newSponsorEvent"}},
            ],
            "nextPageToken": "next-1",
            "pollingIntervalMillis": 5000,
        }
        with patch("backend.app.youtube_live_chat.urlopen", return_value=FakeResponse(payload)):
            batch = self.client.fetch_recent_messages("video123", self.permission, live_chat_id="chat-abc")
        self.assertEqual(len(batch.events), 2)
        self.assertEqual(batch.events[0].event_id, "m1")
        self.assertEqual(batch.events[1].text, "GTA")
        self.assertEqual(batch.next_page_token, "next-1")
        self.assertEqual(batch.polling_interval_ms, 5000)

    def test_permission_is_checked_before_api_access(self):
        revoked = PermissionRecord(
            source_id="video123",
            granted_by="creator",
            scopes=frozenset({"analyze_chat"}),
            granted_at=datetime.now(timezone.utc) - timedelta(hours=2),
            revoked_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        with patch("backend.app.youtube_live_chat.urlopen") as request:
            with self.assertRaises(PermissionError):
                self.client.fetch_recent_messages("video123", revoked, live_chat_id="chat-abc")
            request.assert_not_called()

    def test_rejects_permission_for_another_video(self):
        with self.assertRaises(ValueError):
            self.client.fetch_recent_messages("other-video", self.permission, live_chat_id="chat-abc")

    def test_rejects_out_of_range_page_size(self):
        with self.assertRaises(ValueError):
            self.client.fetch_recent_messages("video123", self.permission, live_chat_id="chat-abc", max_results=20)

    def test_sanitizes_http_errors(self):
        from urllib.error import HTTPError
        error = HTTPError("https://example.invalid/?key=secret", 403, "Forbidden", {}, None)
        error.read = lambda: b'{"error":{"errors":[{"reason":"quotaExceeded"}]}}'
        with patch("backend.app.youtube_live_chat.urlopen", side_effect=error):
            with self.assertRaisesRegex(YouTubeApiError, "quotaExceeded") as raised:
                self.client.get_active_live_chat_id("video123")
        self.assertNotIn("secret", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
