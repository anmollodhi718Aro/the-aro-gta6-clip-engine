"""Fail-closed, OAuth-bound per-clip YouTube upload approval.

Approval records bind the verified Google OIDC subject, destination channel,
clip/source IDs, and exact local video bytes. This module never uploads.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .rights_registry import SourceRightsRegistry


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



def _verify_google_id_token(credentials: Any, oauth_client_id: str) -> dict[str, Any]:
    """Verify the OAuth session's Google ID token signature and audience."""
    claims = _verify_google_id_token(credentials, oauth_client_id)
    return claims


def verify_authenticated_channel_owner(
    credentials: Any,
    youtube: Any,
    *,
    oauth_client_id: str,
    expected_google_subject: str,
    expected_channel_id: str,
) -> AuthenticatedChannelOwner:
    """Verify the Google OIDC principal and its OAuth-backed YouTube channel."""
    required = (oauth_client_id, expected_google_subject, expected_channel_id)
    if not all(isinstance(value, str) and value.strip() for value in required):
        raise PermissionError("configured Google owner subject, OAuth client ID and YouTube channel ID are required")
    token = getattr(credentials, "id_token", None)
    if not isinstance(token, str) or not token:
        raise PermissionError("OAuth session has no OpenID Connect identity token")
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import id_token

        claims = id_token.verify_oauth2_token(token, Request(), audience=oauth_client_id)
    except Exception as exc:
        raise PermissionError("Google identity token could not be verified") from exc
    if not isinstance(claims, dict):
        raise PermissionError("verified Google identity token claims are invalid")
    subject = claims.get("sub")
    issuer = claims.get("iss")
    authorized_party = claims.get("azp")
    if (
        not isinstance(subject, str)
        or not subject
        or issuer not in ("accounts.google.com", "https://accounts.google.com")
        or (authorized_party is not None and authorized_party != oauth_client_id)
    ):
        raise PermissionError("verified Google identity token is missing a valid subject, issuer or authorized party")
    if subject != expected_google_subject:
        raise PermissionError("authenticated Google account is not the configured channel owner")
    try:
        response = youtube.channels().list(part="id", mine=True).execute()
        items = response.get("items", [])
        channel_ids = [
            item.get("id") for item in items
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
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
    privacy: str,
    confirmed: bool,
    at: datetime | None = None,
    expires_at: datetime | None = None,
) -> dict[str, Any]:
    """Persist a one-time owner decision; never overwrite an existing record."""
    if confirmed is not True:
        raise PermissionError("explicit channel-owner confirmation is required")
    if privacy not in {"private", "unlisted", "public"}:
        raise ValueError("approval privacy must be private, unlisted or public")
    if not all(isinstance(value, str) and value.strip() for value in (
        clip_id, source_id, owner.google_subject, owner.channel_id
    )):
        raise ValueError("clip, source and authenticated owner identities are required")
    reviewed_at = at or datetime.now(timezone.utc)
    expiry = expires_at or (reviewed_at + timedelta(hours=24))
    if reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
        raise ValueError("approval timestamp must be timezone-aware")
    if expiry.tzinfo is None or expiry.utcoffset() is None or expiry <= reviewed_at:
        raise ValueError("approval expiry must be timezone-aware and later than review time")
    record = {
        "schema_version": 1,
        "decision": "approved",
        "clip_id": clip_id.strip(),
        "source_id": source_id.strip(),
        "privacy": privacy,
        "source_sha256": sha256_file(video_path),
        "reviewer_google_subject": owner.google_subject,
        "reviewer_channel_id": owner.channel_id,
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
        # A hard link atomically publishes the complete record and refuses
        # to replace an existing approval at this path.
        os.link(temp_name, target)
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
    privacy: str,
    rights_registry: SourceRightsRegistry,
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
        "privacy": privacy,
        "source_sha256": sha256_file(video_path),
        "reviewer_google_subject": owner.google_subject,
        "reviewer_channel_id": owner.channel_id,
        "destination_channel_id": owner.channel_id,
    }
    if any(record.get(key) != value for key, value in expected.items()):
        raise PermissionError("owner approval does not match the authenticated account, channel, clip, source or exact video")
    now = at or datetime.now(timezone.utc)
    reviewed_at = _parse_aware(record.get("reviewed_at"), "reviewed_at")
    expires_at = _parse_aware(record.get("expires_at"), "expires_at")
    if reviewed_at > now or expires_at <= now or expires_at <= reviewed_at:
        raise PermissionError("owner approval is expired or has an invalid review time")
    if not isinstance(rights_registry, SourceRightsRegistry):
        raise PermissionError("current source publish permission registry is required")
    rights_registry.authorize(source_id, "publish", "youtube", at=now)
