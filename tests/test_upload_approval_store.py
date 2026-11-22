"""Tests for immutable upload approval and permission records."""
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from pathlib import Path

from backend.app.approval import ApprovalStatus, UploadApproval
from backend.app.upload_approval_store import (
    load_publish_permission, load_upload_approval, save_upload_approval,
)


class UploadApprovalStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.key_patch = patch.dict(os.environ, {\"ARO_UPLOAD_APPROVAL_KEY\": \"test-only-signing-key-with-32-bytes-minimum\"})
        self.key_patch.start()

    def tearDown(self):
        self.key_patch.stop()
        self.temp.cleanup()

    def test_round_trip_preserves_clip_source_owner_and_timestamp(self):
        approval = UploadApproval(
            clip_id="clip-001", source_id="source-001",
            status=ApprovalStatus.APPROVED, reviewed_by="UC_OWNER",
            reviewed_at=datetime(2026, 11, 22, 9, 0, tzinfo=timezone.utc),
        )
        path = save_upload_approval(self.root / "approval.json", approval)
        loaded = load_upload_approval(path)
        self.assertEqual(loaded, approval)

    def test_record_is_immutable_and_cannot_be_overwritten(self):
        approval = UploadApproval(
            clip_id="clip-001", source_id="source-001",
            status=ApprovalStatus.APPROVED, reviewed_by="UC_OWNER",
            reviewed_at=datetime.now(timezone.utc),
        )
        path = self.root / "approval.json"
        save_upload_approval(path, approval)
        with self.assertRaises(FileExistsError):
            save_upload_approval(path, approval)

    def test_pending_approval_cannot_be_persisted(self):
        approval = UploadApproval(clip_id="clip-001", source_id="source-001")
        with self.assertRaisesRegex(ValueError, "final approval"):
            save_upload_approval(self.root / "approval.json", approval)

    def test_malformed_or_incomplete_approval_fails_closed(self):
        path = self.root / "bad.json"
        path.write_text(json.dumps({"clip_id": "clip-001"}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "required schema"):
            load_upload_approval(path)

    def test_tampered_approval_is_rejected(self):
        approval = UploadApproval(
            clip_id="clip-001", source_id="source-001",
            status=ApprovalStatus.APPROVED, reviewed_by="UC_OWNER",
            reviewed_at=datetime.now(timezone.utc),
        )
        path = save_upload_approval(self.root / "approval.json", approval)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["reviewed_by"] = "ATTACKER_SUPPLIED_ID"
        path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(PermissionError, "integrity check"):
            load_upload_approval(path)

    def test_missing_signing_key_fails_closed(self):
        approval = UploadApproval(
            clip_id="clip-001", source_id="source-001",
            status=ApprovalStatus.APPROVED, reviewed_by="UC_OWNER",
            reviewed_at=datetime.now(timezone.utc),
        )
        with patch.dict(os.environ, {"ARO_UPLOAD_APPROVAL_KEY": ""}):
            with self.assertRaisesRegex(PermissionError, "must be configured"):
                save_upload_approval(self.root / "approval.json", approval)

    def test_permission_record_uses_timezone_aware_model(self):
        path = self.root / "permission.json"
        path.write_text(json.dumps({
            "source_id": "source-001", "granted_by": "creator-001",
            "scopes": ["publish"], "granted_at": "2026-11-22T00:00:00+00:00",
            "expires_at": None, "revoked_at": None,
        }), encoding="utf-8")
        permission = load_publish_permission(path)
        self.assertTrue(permission.allows("publish", datetime.now(timezone.utc)))


if __name__ == "__main__":
    unittest.main()
