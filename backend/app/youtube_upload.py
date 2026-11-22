"""Explicitly approved YouTube Data API upload for local authorized videos.

An upload requires a durable per-clip approval, an active publish permission,
and an approval reviewer matching the channel identity returned by YouTube's
authenticated channels.list(mine=True) endpoint. Boolean CLI acknowledgements
are never treated as identity authentication.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .approval import ApprovalStatus, UploadApproval, require_upload_approval
from .models import PermissionRecord, parse_datetime


UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
CHANNEL_READ_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
OAUTH_SCOPES = [UPLOAD_SCOPE, CHANNEL_READ_SCOPE]
DEFAULT_CATEGORY_ID = "20"  # Gaming


def load_rights_report(path: str | Path) -> dict[str, Any]:
    report_path = Path(path).expanduser()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("rights report must be a JSON object")
    if payload.get("status") != "ready_for_human_review":
        raise PermissionError("rights preflight is not ready for human review")
    if payload.get("platform") != "youtube":
        raise PermissionError("rights preflight must target the youtube platform")
    if payload.get("errors"):
        raise PermissionError("rights preflight contains blocking errors")
    assets = payload.get("assets")
    if not isinstance(assets, list) or not assets:
        raise PermissionError("rights preflight must contain at least one declared visual asset")
    allowed_asset_statuses = {
        "declared_original_requires_human_confirmation",
        "scope_match_metadata_only",
    }
    for index, asset in enumerate(assets, start=1):
        if not isinstance(asset, dict) or asset.get("status") not in allowed_asset_statuses:
            raise PermissionError(f"rights preflight asset {index} is not cleared for human review")
    review = payload.get("review")
    required_reviews = (
        "permission_evidence_human_verification_required",
        "all_embedded_music_and_third_party_rights_review_required",
        "original_asset_declarations_human_confirmation_required",
        "human_edit_and_platform_policy_review_required",
    )
    if not isinstance(review, dict) or review.get("approved_for_upload") is not False:
        raise PermissionError("rights report must remain an unapproved human-review record")
    if not all(review.get(key) is True for key in required_reviews):
        raise PermissionError("rights report is missing mandatory human-review gates")
    return payload


def build_upload_body(
    *,
    title: str,
    description: str,
    tags: list[str],
    privacy: str,
    made_for_kids: bool,
) -> dict[str, Any]:
    clean_title = title.strip()
    if not clean_title or len(clean_title) > 100:
        raise ValueError("title must contain 1 to 100 characters")
    if len(description) > 5000:
        raise ValueError("description must be 5000 characters or fewer")
    if privacy not in {"private", "unlisted", "public"}:
        raise ValueError("privacy must be private, unlisted, or public")
    clean_tags = [str(tag).strip() for tag in tags if str(tag).strip()]
    if any(len(tag) > 100 for tag in clean_tags):
        raise ValueError("each tag must be 100 characters or fewer")
    if sum(len(tag) for tag in clean_tags) > 500:
        raise ValueError("combined tag text must be 500 characters or fewer")
    return {
        "snippet": {
            "title": clean_title,
            "description": description.strip(),
            "tags": clean_tags,
            "categoryId": DEFAULT_CATEGORY_ID,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": bool(made_for_kids),
        },
    }


def validate_upload(
    video_path: str | Path,
    rights_report_path: str | Path,
    *,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    privacy: str = "private",
    made_for_kids: bool,
    owner_approved: bool = False,
    rights_confirmed: bool = False,
    upload_requested: bool = False,
) -> tuple[Path, dict[str, Any]]:
    """Validate local media and rights metadata before any OAuth or network action."""
    video = Path(video_path).expanduser()
    if not video.is_file():
        raise FileNotFoundError(f"local video file does not exist: {video}")
    if video.stat().st_size <= 0:
        raise ValueError("video file is empty")
    mime_type, _ = mimetypes.guess_type(video.name)
    if not mime_type or not mime_type.startswith("video/"):
        raise ValueError("video path must have a recognized video file extension")
    load_rights_report(rights_report_path)
    body = build_upload_body(
        title=title, description=description, tags=tags or [],
        privacy=privacy, made_for_kids=made_for_kids,
    )
    if upload_requested and not owner_approved:
        raise PermissionError("actual upload requires the additional --owner-approved acknowledgement")
    if upload_requested and not rights_confirmed:
        raise PermissionError("actual upload requires the additional --confirm-rights acknowledgement")
    return video, body


def load_upload_approval(path: str | Path) -> UploadApproval:
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("approval record must be a JSON object")
    try:
        return UploadApproval(
            clip_id=payload["clip_id"],
            source_id=payload["source_id"],
            status=ApprovalStatus(payload["status"]),
            reviewed_by=payload.get("reviewed_by"),
            reviewed_at=parse_datetime(payload["reviewed_at"]) if payload.get("reviewed_at") else None,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid approval record: {exc}") from exc


def load_publish_permission(path: str | Path) -> PermissionRecord:
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("publish permission record must be a JSON object")
    try:
        return PermissionRecord.from_dict(payload)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid publish permission record: {exc}") from exc


def save_upload_approval(
    path: str | Path,
    *,
    clip_id: str,
    source_id: str,
    approved: bool,
    authenticated_owner_identity: str,
    at: datetime | None = None,
) -> UploadApproval:
    """Create one immutable approval record, refusing to overwrite an existing decision."""
    pending = UploadApproval(clip_id=clip_id, source_id=source_id)
    decision = pending.decide(
        approved, authenticated_owner_identity, at=at or datetime.now(timezone.utc)
    )
    record_path = Path(path).expanduser()
    record_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "clip_id": decision.clip_id,
        "source_id": decision.source_id,
        "status": decision.status.value,
        "reviewed_by": decision.reviewed_by,
        "reviewed_at": decision.reviewed_at.isoformat(),
    }
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(record_path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except Exception:
        try:
            record_path.unlink()
        except OSError:
            pass
        raise
    return decision


def _authorize_google(client_secrets: Path, token_path: Path):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise RuntimeError(
            'Google upload dependencies are missing. Install with: pip install -e ".[youtube-upload]"'
        ) from exc

    credentials = None
    if token_path.is_file():
        try:
            credentials = Credentials.from_authorized_user_file(str(token_path), OAUTH_SCOPES)
        except (OSError, ValueError):
            credentials = None

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        if not client_secrets.is_file():
            raise FileNotFoundError(
                f"OAuth client file not found: {client_secrets}. Create a Desktop OAuth client in Google Cloud and store it locally."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), OAUTH_SCOPES)
        credentials = flow.run_local_server(
            host="127.0.0.1", port=0, open_browser=True,
            authorization_prompt_message="Authorize THE ARO Studio in your browser: {url}",
        )
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
        try:
            os.chmod(token_path, 0o600)
        except OSError:
            pass
    return credentials


def _build_youtube(client_secrets: Path, token_path: Path):
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            'Google upload dependencies are missing. Install with: pip install -e ".[youtube-upload]"'
        ) from exc
    credentials = _authorize_google(client_secrets, token_path)
    return build("youtube", "v3", credentials=credentials, cache_discovery=False)


def authenticated_channel_identity(youtube: Any) -> str:
    """Resolve the channel subject from the authenticated YouTube session."""
    response = youtube.channels().list(part="id", mine=True).execute()
    items = response.get("items", []) if isinstance(response, dict) else []
    if not isinstance(items, list) or len(items) != 1:
        raise PermissionError("OAuth session must resolve to exactly one destination channel")
    channel_id = str(items[0].get("id", "")).strip() if isinstance(items[0], dict) else ""
    if not channel_id:
        raise PermissionError("authenticated YouTube channel identity is missing")
    return channel_id


def upload_video(
    video_path: Path,
    body: dict[str, Any],
    *,
    client_secrets: Path,
    token_path: Path,
    approval_path: Path,
    permission_path: Path,
    clip_id: str,
    source_id: str,
    youtube_client: Any | None = None,
    at: datetime | None = None,
) -> dict[str, str]:
    """Re-check owner identity, exact-clip approval and active publish scope immediately before insert."""
    youtube = youtube_client or _build_youtube(client_secrets, token_path)
    owner_identity = authenticated_channel_identity(youtube)
    approval = load_upload_approval(approval_path)
    permission = load_publish_permission(permission_path)
    if approval.clip_id != clip_id or approval.source_id != source_id:
        raise PermissionError("approval record does not match the requested clip and source")
    require_upload_approval(
        approval, permission, owner_identity=owner_identity, at=at
    )
    mime_type, _ = mimetypes.guess_type(video_path.name)
    media = _media_upload(video_path, mime_type or "application/octet-stream")
    response = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    ).execute(num_retries=3)
    video_id = str(response.get("id", "")).strip()
    if not video_id:
        raise RuntimeError("YouTube API response did not include a video ID")
    return {"video_id": video_id, "url": f"https://www.youtube.com/watch?v={video_id}"}


def _media_upload(video_path: Path, mime_type: str):
    from googleapiclient.http import MediaFileUpload
    return MediaFileUpload(
        str(video_path),
        mimetype=mime_type,
        chunksize=8 * 1024 * 1024,
        resumable=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run, record authenticated per-clip approval, or upload one local video through YouTube Data API v3."
    )
    parser.add_argument("video", type=Path, help="Local video file. Remote URLs are not supported.")
    parser.add_argument("--rights-report", type=Path, required=True,
                        help="Human-review-ready rights preflight JSON report")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--privacy", choices=("private", "unlisted", "public"), default="private")
    made_for_kids = parser.add_mutually_exclusive_group(required=True)
    made_for_kids.add_argument("--made-for-kids", dest="made_for_kids", action="store_true")
    made_for_kids.add_argument("--not-made-for-kids", dest="made_for_kids", action="store_false")
    parser.add_argument("--client-secrets", type=Path, default=Path("client_secret.json"))
    parser.add_argument("--token", type=Path, default=Path("token.json"))
    parser.add_argument("--approval-record", type=Path, help="Durable per-clip approval JSON path")
    parser.add_argument("--permission-record", type=Path, help="Active source publish-permission JSON path")
    parser.add_argument("--clip-id")
    parser.add_argument("--source-id")
    decision = parser.add_mutually_exclusive_group()
    decision.add_argument("--approve-clip", action="store_true", help="Record approval using the authenticated channel identity")
    decision.add_argument("--reject-clip", action="store_true", help="Record rejection using the authenticated channel identity")
    parser.add_argument("--upload", action="store_true", help="Perform an API upload; default is dry-run only")
    parser.add_argument("--owner-approved", action="store_true",
                        help="Additional acknowledgement only; not identity authentication or an approval record")
    parser.add_argument("--confirm-rights", action="store_true",
                        help="Additional acknowledgement that the exact local video/assets are cleared")
    args = parser.parse_args()

    try:
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        video, body = validate_upload(
            args.video, args.rights_report, title=args.title,
            description=args.description, tags=tags, privacy=args.privacy,
            made_for_kids=args.made_for_kids,
            owner_approved=args.owner_approved,
            rights_confirmed=args.confirm_rights,
            upload_requested=args.upload,
        )
        if args.approve_clip or args.reject_clip:
            if args.upload:
                raise ValueError("approval recording and upload must be separate invocations")
            if not args.approval_record or not args.clip_id or not args.source_id:
                raise ValueError("--approval-record, --clip-id and --source-id are required to record a decision")
            youtube = _build_youtube(args.client_secrets.expanduser(), args.token.expanduser())
            owner_identity = authenticated_channel_identity(youtube)
            approval = save_upload_approval(
                args.approval_record,
                clip_id=args.clip_id,
                source_id=args.source_id,
                approved=args.approve_clip,
                authenticated_owner_identity=owner_identity,
            )
            print(json.dumps({"status": approval.status.value, "clip_id": approval.clip_id,
                              "source_id": approval.source_id, "reviewed_by": approval.reviewed_by,
                              "reviewed_at": approval.reviewed_at.isoformat()}, indent=2))
            return 0
        if not args.upload:
            print(json.dumps({
                "status": "dry_run_validated",
                "video_file": video.name,
                "metadata": body,
                "upload_performed": False,
                "next_step": "Obtain a durable authenticated owner approval and active publish permission before any upload.",
            }, ensure_ascii=False, indent=2))
            return 0
        if not args.owner_approved or not args.confirm_rights:
            raise PermissionError("upload requires both additional acknowledgement flags")
        if not args.approval_record or not args.permission_record or not args.clip_id or not args.source_id:
            raise ValueError("--approval-record, --permission-record, --clip-id and --source-id are required for upload")
        result = upload_video(
            video, body,
            client_secrets=args.client_secrets.expanduser(),
            token_path=args.token.expanduser(),
            approval_path=args.approval_record,
            permission_path=args.permission_record,
            clip_id=args.clip_id,
            source_id=args.source_id,
        )
        print(json.dumps({"status": "uploaded", **result}, indent=2))
        return 0
    except (OSError, ValueError, PermissionError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"YouTube upload stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
