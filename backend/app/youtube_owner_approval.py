"""Fail-closed, OAuth-bound per-clip YouTube upload approval.

The Google OIDC subject and the YouTube channel ID are verified from the
current OAuth credentials. Approval records are bound to the exact clip,
source and SHA-256 of the local rendered file. This module never uploads.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class AuthenticatedChannelOwner:
    google_subject: str
    channel_id: str


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_authenticated_channel_owner(
    credentials: Any,
    youtube: Any,
    *,
    oauth_client_id: str,
    expected_google_subject: str,
    expected_channel_id: str,
) -> AuthenticatedChannelOwner:
    """Verify the OIDC principal and the channel returned by channels.list(mine=True)."""
    if not all(isinstance(value, str) and value.strip() for value in (
        oauth_client_id, expected_google_subject, expected_channel_id
    )):
        raise PermissionError("configured Google owner subject and YouTube channel ID are required")
    token = getattr(credentials, "id_token", None)
    if not isinstance(token, str) or not token:
        raise PermissionError("OAuth session has no OpenID Connect identity token")
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import id_token
        claims = id_token.verify_oauth2_token(token, Request(), audience=oauth_client_id)
    except Exception as exc:
        raise PermissionError("Google identity token could not be verified") from exc
    subject = claims.get("sub") if isinstance(claims, dict) else None
    issuer = claims.get("iss") if isinstance(claims, dict) else None
    if not isinstance(subject, str) or not subject or issuer not in (
        "accounts.google.com", "https://accounts.google.com"
    ):
        raise PermissionError("verified Google identity token is missing a valid subject or issuer")
    if subject != expected_google_subject:
        raise PermissionError("authenticated Google account is not the configured channel owner")
    try:
        response = youtube.channels().list(part="id", mine=True).execute()
        items = response.get("items", [])
        channel_ids = [item.get("id") for item in items if isinstance(item, dict)]
    except Exception as exc:
        raise PermissionError("could not verify the OAuth account's YouTube channel") from exc
    if expected_channel_id not in channel_ids:
        raise PermissionError("OAuth account does not resolve to the configured destination channel")
    return AuthenticatedChannelOwner(subject, expected_channel_id)


def _parse_aware(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise PermissionError(f"{field} is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PermissionError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PermissionError(f"{field} must include a timezone")
    return parsed


def write_owner_approval_record(
    path: str | Path,
    *,
    clip_id: str,
    source_id: str,
    video_path: str | Path,
    owner: AuthenticatedChannelOwner,
    confirmed: bool,
    at: datetime | None = None,
    expires_at: datetime | None = None,
) -> dict[str, Any]:
    """Persist an explicit owner decision; caller must obtain confirmation in trusted UI."""
    if confirmed is not True:
        raise PermissionError("explicit channel-owner confirmation is required")
    if not clip_id.strip() or not source_id.strip() or not owner.google_subject or not owner.channel_id:
        raise ValueError("clip, source and authenticated owner identities are required")
    reviewed_at = at or datetime.now(timezone.utc)
    expiry = expires_at or reviewed_at.replace(microsecond=0)
    if reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
        raise ValueError("approval timestamp must be timezone-aware")
    if expiry.tzinfo is None or expiry.utcoffset() is None or expiry <= reviewed_at:
        raise ValueError("approval expiry must be timezone-aware and later than review time")
    record = {
        "schema_version": 1,
        "decision": "approved",
        "clip_id": clip_id.strip(),
        "source_id": source_id.strip(),
        "source_sha256": sha256_file(video_path),
        "reviewer_google_subject": owner.google_subject,
        "destination_channel_id": owner.channel_id,
        "reviewed_at": reviewed_at.astimezone(timezone.utc).isoformat(),
        "expires_at": expiry.astimezone(timezone.utc).isoformat(),
    }
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, target)
        try:
            os.chmod(target, 0o600)
        except OSError:
            pass
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return record


def require_current_owner_approval(
    approval_path: str | Path,
    *,
    clip_id: str,
    source_id: str,
    video_path: str | Path,
    owner: AuthenticatedChannelOwner,
    permission_evidence: Mapping[str, Any],
    at: datetime | None = None,
) -> None:
    """Fail closed on stale, mismatched, revoked or non-publishable evidence."""
    try:
        record = json.loads(Path(approval_path).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PermissionError("durable owner approval record is missing or unreadable") from exc
    if not isinstance(record, dict) or record.get("schema_version") != 1:
        raise PermissionError("owner approval record has an unsupported schema")
    expected = {
        "decision": "approved",
        "clip_id": clip_id,
        "source_id": source_id,
        "source_sha256": sha256_file(video_path),
        "reviewer_google_subject": owner.google_subject,
        "destination_channel_id": owner.channel_id,
    }
    if any(record.get(key) != value for key, value in expected.items()):
        raise PermissionError("owner approval does not match the authenticated owner, clip, source or exact video")
    now = at or datetime.now(timezone.utc)
    reviewed_at = _parse_aware(record.get("reviewed_at"), "reviewed_at")
    expires_at = _parse_aware(record.get("expires_at"), "expires_at")
    if reviewed_at > now or expires_at <= now or expires_at <= reviewed_at:
        raise PermissionError("owner approval is expired or has an invalid review time")
    if not isinstance(permission_evidence, Mapping):
        raise PermissionError("current source publish permission evidence is required")
    if permission_evidence.get("source_id") != source_id:
        raise PermissionError("publish permission does not match the clip source")
    scopes = permission_evidence.get("scopes")
    if permission_evidence.get("status") != "active" or permission_evidence.get("revoked") is not False:
        raise PermissionError("source publish permission is inactive or revoked")
    if not isinstance(scopes, list) or "publish" not in scopes:
        raise PermissionError("current publish scope is required")
    permission_expiry = _parse_aware(permission_evidence.get("expires_at"), "permission expires_at")
    if permission_expiry <= now:
        raise PermissionError("source publish permission has expired")
