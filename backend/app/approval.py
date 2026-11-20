"""Immutable human approval gate for public upload operations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .models import PermissionRecord


class ApprovalStatus(str, Enum):
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class UploadApproval:
    clip_id: str
    source_id: str
    status: ApprovalStatus = ApprovalStatus.NEEDS_REVIEW
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.clip_id, str) or not self.clip_id.strip():
            raise ValueError("clip_id is required")
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id is required")
        if self.status == ApprovalStatus.NEEDS_REVIEW:
            if self.reviewed_by is not None or self.reviewed_at is not None:
                raise ValueError("unreviewed items cannot contain reviewer metadata")
        else:
            if not isinstance(self.reviewed_by, str) or not self.reviewed_by.strip() or self.reviewed_at is None:
                raise ValueError("a final decision requires reviewer and timestamp")
            if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
                raise ValueError("reviewed_at must include a timezone")

    def decide(
        self, approved: bool, reviewer: str, *, at: datetime | None = None
    ) -> "UploadApproval":
        if self.status != ApprovalStatus.NEEDS_REVIEW:
            raise ValueError("approval has already received a final decision")
        if not isinstance(approved, bool):
            raise ValueError("approved must be a boolean decision")
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("reviewer is required")
        return UploadApproval(
            clip_id=self.clip_id,
            source_id=self.source_id,
            status=ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED,
            reviewed_by=reviewer.strip(),
            reviewed_at=at or datetime.now(timezone.utc),
        )


def require_upload_approval(
    approval: UploadApproval,
    permission: PermissionRecord,
    *,
    owner_identity: str,
    at: datetime | None = None,
) -> None:
    """Require approval by the authenticated channel owner and an active publish grant.

    owner_identity must come from a trusted server-side authentication
    context (for example, the verified platform account subject). It must not
    come from a client-supplied form field or an unverified display name.
    This function compares identities; it does not authenticate the caller.
    """
    if not isinstance(owner_identity, str) or not owner_identity.strip():
        raise ValueError("trusted channel owner identity is required")
    now = at or datetime.now(timezone.utc)
    if approval.status != ApprovalStatus.APPROVED:
        raise PermissionError("owner approval is required before upload")
    if approval.reviewed_by != owner_identity:
        raise PermissionError("approval was not recorded by the authenticated channel owner")
    if permission.source_id != approval.source_id:
        raise PermissionError("upload permission does not match clip source")
    if not permission.allows("publish", now):
        raise PermissionError("active publish permission is required")
