"""Durable, integrity-checked local approval and permission records.

Approval reviewer identities are populated only after OAuth resolves the
authenticated destination channel. HMAC protects records against local edits.
The signing key is supplied through ARO_UPLOAD_APPROVAL_KEY, never Git.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .approval import ApprovalStatus, UploadApproval
from .models import PermissionRecord


def _signing_key() -> bytes:
    value = os.environ.get("ARO_UPLOAD_APPROVAL_KEY", "")
    if len(value.encode("utf-8")) < 32:
        raise PermissionError(
            "ARO_UPLOAD_APPROVAL_KEY must be configured with at least 32 bytes"
        )
    return value.encode("utf-8")


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def load_upload_approval(path: str | Path) -> UploadApproval:
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("approval record must be a JSON object")
    required = {"clip_id", "source_id", "status", "reviewed_by", "reviewed_at", "signature"}
    if set(payload) != required:
        raise ValueError("approval record fields do not match the required schema")
    signature = payload.pop("signature")
    expected = hmac.new(_signing_key(), _canonical_json(payload), hashlib.sha256).hexdigest()
    if not isinstance(signature, str) or not hmac.compare_digest(signature, expected):
        raise PermissionError("approval record integrity check failed")
    try:
        status = ApprovalStatus(payload["status"])
    except (TypeError, ValueError) as exc:
        raise ValueError("approval record has an invalid decision") from exc
    try:
        reviewed_at = datetime.fromisoformat(str(payload["reviewed_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("approval record timestamp is invalid") from exc
    return UploadApproval(
        clip_id=payload["clip_id"],
        source_id=payload["source_id"],
        status=status,
        reviewed_by=payload["reviewed_by"],
        reviewed_at=reviewed_at,
    )


def load_publish_permission(path: str | Path) -> PermissionRecord:
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("permission record must be a JSON object")
    return PermissionRecord.from_dict(payload)


def save_upload_approval(path: str | Path, approval: UploadApproval) -> Path:
    """Create an immutable signed approval file; never overwrite a decision."""
    if approval.status == ApprovalStatus.NEEDS_REVIEW:
        raise ValueError("only a final approval decision can be persisted")
    payload: dict[str, Any] = {
        "clip_id": approval.clip_id,
        "source_id": approval.source_id,
        "status": approval.status.value,
        "reviewed_by": approval.reviewed_by,
        "reviewed_at": approval.reviewed_at.isoformat(),
    }
    signature = hmac.new(_signing_key(), _canonical_json(payload), hashlib.sha256).hexdigest()
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents silently replacing a prior decision.
    with target.open("x", encoding="utf-8") as stream:
        json.dump({**payload, "signature": signature}, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    try:
        os.chmod(target, 0o600)
    except OSError:
        pass
    return target
