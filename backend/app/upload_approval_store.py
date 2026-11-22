"""Durable local approval and source-permission records for YouTube uploads.

Approval reviewer identities are populated only after OAuth resolves the
authenticated destination channel. Records are immutable once created.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .approval import ApprovalStatus, UploadApproval
from .models import PermissionRecord


def load_upload_approval(path: str | Path) -> UploadApproval:
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("approval record must be a JSON object")
    required = {"clip_id", "source_id", "status", "reviewed_by", "reviewed_at"}
    if set(payload) != required:
        raise ValueError("approval record fields do not match the required schema")
    try:
        status = ApprovalStatus(payload["status"])
    except (TypeError, ValueError) as exc:
        raise ValueError("approval record has an invalid decision") from exc
    from datetime import datetime
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
    """Create an immutable approval file; never overwrite an existing decision."""
    if approval.status == ApprovalStatus.NEEDS_REVIEW:
        raise ValueError("only a final approval decision can be persisted")
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "clip_id": approval.clip_id,
        "source_id": approval.source_id,
        "status": approval.status.value,
        "reviewed_by": approval.reviewed_by,
        "reviewed_at": approval.reviewed_at.isoformat(),
    }
    # Exclusive creation prevents silently replacing a prior decision.
    with target.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\\n")
    try:
        os.chmod(target, 0o600)
    except OSError:
        pass
    return target
