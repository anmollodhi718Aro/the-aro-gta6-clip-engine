"""Fail-closed validation for locally supplied, explicitly authorized media assets."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import PermissionRecord, parse_datetime


def validate_authorized_media_asset(
    media_path: str | Path,
    permission: PermissionRecord,
    source_id: str,
    approved_at: datetime,
) -> Path:
    """Return a local file only when the matching permission allows media processing.

    This function does not download, decode, render, or publish media. The caller
    must supply a local path and a permission record with the process_media scope.
    """
    if not source_id.strip() or source_id != permission.source_id:
        raise ValueError("media source does not match the permission record")

    timestamp = parse_datetime(approved_at)
    if not permission.allows("process_media", timestamp):
        raise PermissionError(
            "media-processing permission is missing, expired, revoked, or out of scope"
        )

    candidate = Path(media_path).expanduser()
    if candidate.is_symlink():
        raise ValueError("symbolic links are not accepted as media assets")

    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("media asset must be an existing local file") from exc

    if not resolved.is_file():
        raise ValueError("media asset must be a regular local file")

    return resolved
