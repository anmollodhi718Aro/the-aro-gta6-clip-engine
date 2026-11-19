"""Human approval gate for any public upload operation."""
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
        if not self.clip_id.strip() or not self.source_id.strip():
            raise ValueError("clip_id and source_id are required")
        if self.status == ApprovalStatus.NEEDS_REVIEW and (
            self.reviewed_by is not None or self.reviewed_at is not None
        ):
            raise ValueError("unreviewed items cannot contain reviewer metadata")
        if self.status != ApprovalStatus.NEEDS_REVIEW:
            if not self.reviewed_by or not self.reviewed_by.strip() or self.reviewed_at is None:
                raise ValueError("a final decision requires reviewer and timestamp")
            if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
                raise ValueError("reviewed_at must include a timezone")

    def decide(self, approved: bool, reviewer: str, *, at: datetime | None = None) -> "UploadApproval":
        if self.status != ApprovalStatus.NEEDS_REVIEW:
            raise ValueError("approval has already received a final decision")
        if not reviewer.strip():
            raise ValueError("reviewer is required")
        return UploadApproval(
            clip_id=self.clip_id,
            source_id=self.source_id,
            status=ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED,
            reviewed_by=reviewer,
            reviewed_at=at or datetime.now(timezone.utc),
        )


def require_upload_approval(
    approval: UploadApproval,
    permission: PermissionRecord,
    *,
    at: datetime | None = None,
) -> None:
    now = at or datetime.now(timezone.utc)
    if approval.status != ApprovalStatus.APPROVED:
        raise PermissionError("owner approval is required before upload")
    if permission.source_id != approval.source_id:
        raise PermissionError("upload permission does not match clip source")
    if not permission.allows("publish", now):
        raise PermissionError("active publish permission is required")
