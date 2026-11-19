"""Tests for the one-shot YouTube CLI orchestration."""

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from backend.app.consent_registry import ConsentRegistry
from backend.app.models import ChatEvent, PermissionRecord
from backend.app.youtube_live_chat import YouTubeChatBatch
from backend.app.youtube_cli import run


class YouTubeCliTests(unittest.TestCase):
    def test_writes_candidate_plan_and_pagination_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            permission_path = Path(folder) / "permission.json"
            output_path = Path(folder) / "output.json"
            now = datetime.now(timezone.utc)
            permission_path.write_text(json.dumps({
                "source_id": "video123",
                "granted_by": "creator",
                "scopes": ["analyze_chat"],
                "granted_at": (now - timedelta(minutes=1)).isoformat(),
                "expires_at": (now + timedelta(hours=1)).isoformat(),
            }), encoding="utf-8")
            events = tuple(
                ChatEvent(f"e-{i}", "video123", now + timedelta(seconds=i), "synthetic")
                for i in range(1, 10)
            )
            batch = YouTubeChatBatch("video123", "chat123", events, "next-page", 5000, False)
            with patch("backend.app.youtube_cli.YouTubeLiveChatClient") as client_class:
                client_class.return_value.fetch_recent_messages.return_value = batch
                status = run("video123", permission_path, output_path)
            self.assertEqual(status, 0)
            result = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(result["event_count"], 9)
            self.assertEqual(result["next_page_token"], "next-page")
            self.assertFalse(result["publishing_enabled"])
            client_class.return_value.fetch_recent_messages.assert_called_once()

    def test_stops_when_permission_file_is_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "output.json"
            with patch("backend.app.youtube_cli.YouTubeLiveChatClient") as client_class:
                status = run("video123", Path(folder) / "missing.json", output_path)
            self.assertEqual(status, 2)
            client_class.assert_not_called()

    def test_uses_persistent_registry_instead_of_json_permission(self):
        with tempfile.TemporaryDirectory() as folder:
            registry_path = Path(folder) / "consent.sqlite3"
            output_path = Path(folder) / "output.json"
            now = datetime.now(timezone.utc)
            permission = PermissionRecord(
                source_id="video123",
                granted_by="creator",
                scopes=frozenset({"analyze_chat"}),
                granted_at=now - timedelta(minutes=1),
                expires_at=now + timedelta(hours=1),
            )
            ConsentRegistry(registry_path).grant(permission)
            batch = YouTubeChatBatch("video123", "chat123", (), None, 5000, False)
            with patch("backend.app.youtube_cli.YouTubeLiveChatClient") as client_class:
                client_class.return_value.fetch_recent_messages.return_value = batch
                status = run(
                    "video123", None, output_path, registry_path=registry_path
                )
            self.assertEqual(status, 0)
            self.assertTrue(output_path.is_file())
            client_class.return_value.fetch_recent_messages.assert_called_once()

    def test_registry_revocation_blocks_api_call(self):
        with tempfile.TemporaryDirectory() as folder:
            registry_path = Path(folder) / "consent.sqlite3"
            now = datetime.now(timezone.utc)
            registry = ConsentRegistry(registry_path)
            registry.grant(PermissionRecord(
                source_id="video123",
                granted_by="creator",
                scopes=frozenset({"analyze_chat"}),
                granted_at=now - timedelta(minutes=1),
            ))
            registry.revoke("video123", actor="owner")
            with patch("backend.app.youtube_cli.YouTubeLiveChatClient") as client_class:
                status = run(
                    "video123", None, Path(folder) / "output.json",
                    registry_path=registry_path,
                )
            self.assertEqual(status, 2)
            client_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
