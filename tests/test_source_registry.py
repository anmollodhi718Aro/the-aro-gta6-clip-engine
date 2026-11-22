"""Tests for the in-memory source permission registry."""

import unittest
from datetime import datetime, timezone

from backend.app.models import PermissionRecord
from backend.app.source_registry import SourceRegistry


class SourceRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = SourceRegistry()
        self.record = PermissionRecord(
            source_id="synthetic-source",
            granted_by="fixture-owner",
            scopes=frozenset({"analyze_chat"}),
            granted_at=datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
            expires_at=datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc),
        )

    def test_register_and_get_permission_record(self) -> None:
        self.registry.register(self.record)
        self.assertEqual(self.registry.get("synthetic-source"), self.record)

    def test_duplicate_source_is_rejected(self) -> None:
        self.registry.register(self.record)
        with self.assertRaises(ValueError):
            self.registry.register(self.record)

    def test_unknown_source_is_rejected(self) -> None:
        with self.assertRaises(KeyError):
            self.registry.get("missing")

    def test_revoke_disables_permission_after_revocation_time(self) -> None:
        self.registry.register(self.record)
        revoked = self.registry.revoke(
            "synthetic-source",
            datetime(2026, 11, 18, 13, 0, tzinfo=timezone.utc),
        )
        self.assertFalse(revoked.allows(
            "analyze_chat",
            datetime(2026, 11, 18, 13, 1, tzinfo=timezone.utc),
        ))
        self.assertTrue(revoked.allows(
            "analyze_chat",
            datetime(2026, 11, 18, 12, 30, tzinfo=timezone.utc),
        ))

    def test_revocation_before_grant_is_rejected(self) -> None:
        self.registry.register(self.record)
        with self.assertRaises(ValueError):
            self.registry.revoke(
                "synthetic-source",
                datetime(2026, 11, 18, 11, 59, tzinfo=timezone.utc),
            )

    def test_second_revocation_is_rejected(self) -> None:
        self.registry.register(self.record)
        at = datetime(2026, 11, 18, 13, 0, tzinfo=timezone.utc)
        self.registry.revoke("synthetic-source", at)
        with self.assertRaises(ValueError):
            self.registry.revoke("synthetic-source", at)

    def test_list_sources_is_sorted_snapshot(self) -> None:
        second = PermissionRecord(
            source_id="another-source",
            granted_by="fixture-owner",
            scopes=frozenset({"analyze_chat"}),
            granted_at=datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
        )
        self.registry.register(self.record)
        self.registry.register(second)
        self.assertEqual(
            [item.source_id for item in self.registry.list_sources()],
            ["another-source", "synthetic-source"],
        )


if __name__ == "__main__":
    unittest.main()
