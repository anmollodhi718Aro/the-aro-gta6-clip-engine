"""Tests for the local source permission registry."""
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.models import PermissionRecord
from backend.app.sources.registry import SourceRegistry


class SourceRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.registry = SourceRegistry(Path(self.temp.name) / "registry.json")
        self.now = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
        self.permission = PermissionRecord(
            source_id="creator-demo",
            granted_by="creator-owner",
            scopes=frozenset({"analyze_chat"}),
            granted_at=self.now - timedelta(minutes=1),
            expires_at=self.now + timedelta(hours=1),
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def register(self) -> None:
        self.registry.register(
            self.permission,
            permission_reference="consent-ticket-001",
            permitted_uses=("analyze_chat",),
            actor="operator",
        )

    def test_register_and_require_valid_scope(self) -> None:
        self.register()
        record = self.registry.require("creator-demo", "analyze_chat", at=self.now)
        self.assertEqual(record.permission_reference, "consent-ticket-001")
        self.assertEqual(record.permitted_uses, ("analyze_chat",))

    def test_unknown_source_is_rejected(self) -> None:
        with self.assertRaises(KeyError):
            self.registry.require("unknown", "analyze_chat", at=self.now)

    def test_out_of_scope_and_expired_permission_are_rejected(self) -> None:
        self.register()
        with self.assertRaises(PermissionError):
            self.registry.require("creator-demo", "edit_video", at=self.now)
        with self.assertRaises(PermissionError):
            self.registry.require("creator-demo", "analyze_chat", at=self.now + timedelta(hours=2))

    def test_revocation_is_persisted_and_audited(self) -> None:
        self.register()
        self.registry.revoke("creator-demo", actor="operator", at=self.now)
        with self.assertRaises(PermissionError):
            self.registry.require("creator-demo", "analyze_chat", at=self.now)
        self.assertEqual(
            [entry["action"] for entry in self.registry.audit_log()],
            ["source_registered", "source_revoked"],
        )

    def test_duplicate_registration_is_not_silent_overwrite(self) -> None:
        self.register()
        with self.assertRaises(ValueError):
            self.register()

    def test_missing_audit_actor_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.registry.register(
                self.permission,
                permission_reference="consent-ticket-001",
                permitted_uses=("analyze_chat",),
                actor=" ",
            )


if __name__ == "__main__":
    unittest.main()
