"""Owner-authenticated YouTube upload for local, authorized video assets.

Uploads require a durable per-clip approval created in a separate OAuth-authenticated
step, an active source publish grant, explicit rights confirmation, and --upload.
Google OAuth dependencies remain optional until an action is requested.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from .approval import UploadApproval, require_upload_approval
from .upload_approval_store import (
    load_publish_permission, load_upload_approval, save_upload_approval,
)


UPLOAD_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]
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
    rights_confirmed: bool = False,
    upload_requested: bool = False,
) -> tuple[Path, dict[str, Any]]:
    """Validate local media, metadata, rights preflight and explicit approvals."""
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
    if upload_requested and not rights_confirmed:
        raise PermissionError("actual upload requires --confirm-rights")
    return video, body


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
            credentials = Credentials.from_authorized_user_file(str(token_path), UPLOAD_SCOPES)
        except (OSError, ValueError):
            credentials = None

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        if not client_secrets.is_file():
            raise FileNotFoundError(
                f"OAuth client file not found: {client_secrets}. Create a Desktop OAuth client in Google Cloud and store it locally."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), UPLOAD_SCOPES)
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


def _build_youtube_client(credentials):
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            'Google upload dependencies are missing. Install with: pip install -e ".[youtube-upload]"'
        ) from exc
    return build("youtube", "v3", credentials=credentials, cache_discovery=False)


def resolve_authenticated_channel_id(youtube) -> str:
    """Resolve the OAuth-selected channel identity from YouTube, never from CLI text."""
    response = youtube.channels().list(
        part="id", mine=True, maxResults=50
    ).execute(num_retries=0)
    items = response.get("items", [])
    channel_ids = [
        str(item.get("id", "")).strip()
        for item in items
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    ]
    if len(channel_ids) != 1:
        raise PermissionError(
            "OAuth session must resolve to exactly one destination YouTube channel"
        )
    return channel_ids[0]


def record_upload_approval(
    *,
    approval_record: Path,
    permission_record: Path,
    clip_id: str,
    source_id: str,
    expected_channel_id: str,
    client_secrets: Path,
    token_path: Path,
) -> Path:
    """Create an immutable approval only after OAuth identity and interactive owner confirmation."""
    if not clip_id.strip() or not source_id.strip() or not expected_channel_id.strip():
        raise ValueError("clip ID, source ID, and configured channel ID are required")
    credentials = _authorize_google(client_secrets, token_path)
    youtube = _build_youtube_client(credentials)
    owner_identity = resolve_authenticated_channel_id(youtube)
    if owner_identity != expected_channel_id:
        raise PermissionError("OAuth channel does not match the configured destination channel")
    permission = load_publish_permission(permission_record)
    if permission.source_id != source_id or not permission.allows("publish", datetime.now(timezone.utc)):
        raise PermissionError("active publish permission for this source is required")
    confirmation = input(
        f"Approve clip {clip_id!r} from source {source_id!r} for channel {owner_identity!r}? Type APPROVE to confirm: "
    )
    if confirmation.strip() != "APPROVE":
        raise PermissionError("owner did not confirm this exact clip approval")
    pending = UploadApproval(clip_id=clip_id, source_id=source_id)
    decision = pending.decide(True, owner_identity)
    return save_upload_approval(approval_record, decision)


def upload_video(
    video_path: Path,
    body: dict[str, Any],
    *,
    client_secrets: Path,
    token_path: Path,
    approval_record: Path,
    permission_record: Path,
    clip_id: str,
    source_id: str,
    expected_channel_id: str,
) -> dict[str, str]:
    try:
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise RuntimeError(
            'Google upload dependencies are missing. Install with: pip install -e ".[youtube-upload]"'
        ) from exc

    credentials = _authorize_google(client_secrets, token_path)
    youtube = _build_youtube_client(credentials)
    owner_identity = resolve_authenticated_channel_id(youtube)
    if owner_identity != expected_channel_id:
        raise PermissionError("OAuth channel does not match the configured destination channel")
    mime_type, _ = mimetypes.guess_type(video_path.name)
    media = MediaFileUpload(
        str(video_path),
        mimetype=mime_type or "application/octet-stream",
        chunksize=8 * 1024 * 1024,
        resumable=True,
    )
    # Re-read both durable records immediately before constructing the upload request.
    # This catches permission expiry/revocation and changed/missing approvals.
    approval = load_upload_approval(approval_record)
    permission = load_publish_permission(permission_record)
    if approval.clip_id != clip_id or approval.source_id != source_id:
        raise PermissionError("approval record does not match the exact clip and source")
    require_upload_approval(
        approval, permission, owner_identity=owner_identity
    )
    response = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    ).execute(num_retries=3)
    video_id = str(response.get("id", "")).strip()
    if not video_id:
        raise RuntimeError("YouTube API response did not include a video ID")
    return {"video_id": video_id, "url": f"https://www.youtube.com/watch?v={video_id}"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run or explicitly approved upload of one local video through YouTube Data API v3."
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
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--upload", action="store_true", help="Perform an API upload; default is dry-run only.")
    action.add_argument("--record-approval", action="store_true", help="Authenticate the channel owner and create an immutable approval record; does not upload.")
    parser.add_argument("--clip-id", default="", help="Exact clip identifier bound to the approval.")
    parser.add_argument("--source-id", default="", help="Exact creator/source identifier bound to the approval.")
    parser.add_argument("--channel-id", default="", help="Expected destination channel ID; must match the OAuth-selected channel.")
    parser.add_argument("--approval-record", type=Path, help="Path for the immutable per-clip approval JSON.")
    parser.add_argument("--permission-record", type=Path, help="Path to the current source permission JSON.")
    parser.add_argument("--confirm-rights", action="store_true", help="Confirm that the exact local video and all included assets are cleared for this upload.")
    args = parser.parse_args()

    try:
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        video, body = validate_upload(
            args.video, args.rights_report, title=args.title,
            description=args.description, tags=tags, privacy=args.privacy,
            made_for_kids=args.made_for_kids,
            rights_confirmed=args.confirm_rights,
            upload_requested=args.upload,
        )
        if args.record_approval or args.upload:
            if not all((args.clip_id, args.source_id, args.channel_id, args.approval_record, args.permission_record)):
                raise ValueError("approval/upload requires --clip-id, --source-id, --channel-id, --approval-record, and --permission-record")
        if args.record_approval:
            saved = record_upload_approval(
                approval_record=args.approval_record.expanduser(),
                permission_record=args.permission_record.expanduser(),
                clip_id=args.clip_id,
                source_id=args.source_id,
                expected_channel_id=args.channel_id,
                client_secrets=args.client_secrets.expanduser(),
                token_path=args.token.expanduser(),
            )
            print(json.dumps({
                "status": "owner_approval_recorded",
                "approval_file": str(saved),
                "upload_performed": False,
            }, indent=2))
            return 0
        if not args.upload:
            print(json.dumps({
                "status": "dry_run_validated",
                "video_file": video.name,
                "metadata": body,
                "upload_performed": False,
                "next_step": "Review rights, create a separate OAuth-authenticated per-clip approval, then rerun with --upload --confirm-rights.",
            }, ensure_ascii=False, indent=2))
            return 0
        result = upload_video(
            video, body,
            client_secrets=args.client_secrets.expanduser(),
            token_path=args.token.expanduser(),
            approval_record=args.approval_record.expanduser(),
            permission_record=args.permission_record.expanduser(),
            clip_id=args.clip_id,
            source_id=args.source_id,
            expected_channel_id=args.channel_id,
        )
        print(json.dumps({"status": "uploaded", **result}, indent=2))
        return 0
    except (OSError, ValueError, PermissionError, RuntimeError, json.JSONDecodeError, EOFError) as exc:
        print(f"YouTube upload stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
