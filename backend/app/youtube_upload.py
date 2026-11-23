"""Explicitly approved YouTube Data API upload for local authorized videos.

No upload occurs unless --upload, --owner-approved, --confirm-rights, and an
explicit made-for-kids declaration are supplied. Google OAuth dependencies
are optional and are imported only when an upload is requested.
"""
from __future__ import annotations

import argparse
import io
import json
import mimetypes
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
IDENTITY_SCOPES = ["openid", "https://www.googleapis.com/auth/youtube.readonly", UPLOAD_SCOPE]
DEFAULT_CATEGORY_ID = "20"  # Gaming
DEFAULT_MAX_UPLOAD_BYTES = 256 * 1024 * 1024
UPLOAD_COPY_CHUNK_BYTES = 1024 * 1024


def _validate_max_upload_bytes(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("max_upload_bytes must be a positive integer")
    return value


def _copy_stream_with_limit(source: Any, snapshot: Any, max_upload_bytes: int) -> int:
    """Copy a source into the private snapshot without exceeding the memory budget."""
    limit = _validate_max_upload_bytes(max_upload_bytes)
    total = 0
    while True:
        chunk = source.read(UPLOAD_COPY_CHUNK_BYTES)
        if not chunk:
            return total
        if total + len(chunk) > limit:
            raise ValueError(f"video exceeds the configured upload limit of {limit} bytes")
        snapshot.write(chunk)
        total += len(chunk)



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
    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
) -> tuple[Path, dict[str, Any]]:
    """Validate local media, metadata, rights preflight and explicit approvals."""
    video = Path(video_path).expanduser()
    if not video.is_file():
        raise FileNotFoundError(f"local video file does not exist: {video}")
    if video.stat().st_size <= 0:
        raise ValueError("video file is empty")
    limit = _validate_max_upload_bytes(max_upload_bytes)
    if video.stat().st_size > limit:
        raise ValueError(f"video exceeds the configured upload limit of {limit} bytes")
    mime_type, _ = mimetypes.guess_type(video.name)
    if not mime_type or not mime_type.startswith("video/"):
        raise ValueError("video path must have a recognized video file extension")
    load_rights_report(rights_report_path)
    body = build_upload_body(
        title=title, description=description, tags=tags or [],
        privacy=privacy, made_for_kids=made_for_kids,
    )
    if upload_requested and not owner_approved:
        raise PermissionError("actual upload requires --owner-approved")
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
            credentials = Credentials.from_authorized_user_file(str(token_path), IDENTITY_SCOPES)
        except (OSError, ValueError):
            credentials = None

    if credentials and hasattr(credentials, "has_scopes") and not credentials.has_scopes(IDENTITY_SCOPES):
        credentials = None
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid or not getattr(credentials, "id_token", None):
        if not client_secrets.is_file():
            raise FileNotFoundError(
                f"OAuth client file not found: {client_secrets}. Create a Desktop OAuth client in Google Cloud and store it locally."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), IDENTITY_SCOPES)
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



def _oauth_client_id(client_secrets: Path) -> str:
    """Read only the OAuth client ID needed to validate the OIDC audience."""
    try:
        config = json.loads(client_secrets.expanduser().read_text(encoding="utf-8"))
        client_config = config.get("installed", config.get("web", {}))
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        raise PermissionError("OAuth client configuration is unreadable") from exc
    client_id = client_config.get("client_id") if isinstance(client_config, dict) else None
    if not isinstance(client_id, str) or not client_id.strip():
        raise PermissionError("OAuth client ID is missing")
    return client_id


def require_report_publish_permissions(
    report: dict[str, Any], rights_registry: Any, source_id: str
) -> None:
    """Recheck the clip source and all source-bound assets against current publish grants."""
    if report.get("source_id") != source_id:
        raise PermissionError("requested source_id does not match the rights report")
    source_ids = {source_id}
    for asset in report.get("assets", []):
        if asset.get("status") == "scope_match_metadata_only":
            asset_source_id = str(asset.get("source_id", "")).strip()
            if not asset_source_id:
                raise PermissionError("source-bound rights report asset is missing source_id")
            source_ids.add(asset_source_id)
    for current_source_id in sorted(source_ids):
        rights_registry.authorize(current_source_id, "publish", "youtube")


def _approval_confirmation_phrase(clip_id: str, privacy: str) -> str:
    if privacy == "public":
        return f"PUBLISH PUBLIC {clip_id}"
    return f"APPROVE {privacy.upper()} {clip_id}"


def upload_video(
    video_path: Path,
    body: dict[str, Any],
    *,
    client_secrets: Path,
    token_path: Path,
    rights_report_path: Path,
    approval_record_path: Path,
    rights_db_path: Path,
    clip_id: str,
    source_id: str,
    owner_approved: bool,
    rights_confirmed: bool,
    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
) -> dict[str, str]:
    max_upload_bytes = _validate_max_upload_bytes(max_upload_bytes)
    if Path(video_path).stat().st_size > max_upload_bytes:
        raise ValueError(f"video exceeds the configured upload limit of {max_upload_bytes} bytes")
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
    except ImportError as exc:
        raise RuntimeError(
            'Google upload dependencies are missing. Install with: pip install -e ".[youtube-upload]"'
        ) from exc

    from backend.app.youtube_owner_approval import (
        verify_authenticated_channel_owner,
        require_current_owner_approval,
        sha256_bytes,
    )
    from backend.app.rights_registry import SourceRightsRegistry
    if owner_approved is not True or rights_confirmed is not True:
        raise PermissionError("actual upload requires --owner-approved and --confirm-rights")
    privacy = body.get("status", {}).get("privacyStatus")
    if privacy not in {"private", "unlisted", "public"}:
        raise PermissionError("upload privacy must be explicit")
    expected_subject = os.environ.get("ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT", "").strip()
    expected_channel = os.environ.get("ARO_YOUTUBE_CHANNEL_ID", "").strip()
    if not expected_subject or not expected_channel:
        raise PermissionError("ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT and ARO_YOUTUBE_CHANNEL_ID must be configured")
    oauth_client_id = _oauth_client_id(client_secrets)
    mime_type, _ = mimetypes.guess_type(video_path.name)
    current_report = load_rights_report(rights_report_path)
    if not isinstance(clip_id, str) or not clip_id.strip():
        raise PermissionError("requested clip_id is required")
    if not isinstance(source_id, str) or not source_id.strip():
        raise PermissionError("requested source_id is required")
    if current_report.get("clip_id") != clip_id or current_report.get("source_id") != source_id:
        raise PermissionError("requested clip/source IDs do not match the rights report")

    # Bound and snapshot the bytes before starting OAuth or constructing an API
    # client. Oversized or growing sources therefore fail without opening an
    # interactive auth flow or touching the upload API.
    with tempfile.TemporaryDirectory(prefix="aro-youtube-upload-") as staging_dir:
        snapshot_path = Path(staging_dir) / "approved-upload.mp4"
        with Path(video_path).open("rb") as source, snapshot_path.open("xb") as snapshot:
            _copy_stream_with_limit(source, snapshot, max_upload_bytes)
            snapshot.flush()
            os.fsync(snapshot.fileno())
        try:
            os.chmod(snapshot_path, 0o400)
        except OSError:
            pass
        with snapshot_path.open("rb") as snapshot_stream:
            upload_bytes = snapshot_stream.read()
    upload_sha256 = sha256_bytes(upload_bytes)

    credentials = _authorize_google(client_secrets, token_path)
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    owner = verify_authenticated_channel_owner(
        credentials, youtube, oauth_client_id=oauth_client_id,
        expected_google_subject=expected_subject, expected_channel_id=expected_channel,
    )
    rights_registry = SourceRightsRegistry(rights_db_path.expanduser())
    require_report_publish_permissions(current_report, rights_registry, source_id)
    require_current_owner_approval(
        approval_record_path, clip_id=clip_id, source_id=source_id,
        video_sha256=upload_sha256, owner=owner, privacy=privacy,
        rights_registry=rights_registry,
    )
    # Repeat all identity, approval and current-rights checks immediately
    # before constructing the request. The in-memory bytes cannot be changed
    # by later filesystem mutations of either source or staging.
    owner = verify_authenticated_channel_owner(
        credentials, youtube, oauth_client_id=oauth_client_id,
        expected_google_subject=expected_subject, expected_channel_id=expected_channel,
    )
    require_current_owner_approval(
        approval_record_path, clip_id=clip_id, source_id=source_id,
        video_sha256=upload_sha256, owner=owner, privacy=privacy,
        rights_registry=rights_registry,
    )
    require_report_publish_permissions(current_report, rights_registry, source_id)

    media_stream = io.BytesIO(upload_bytes)
    media = MediaIoBaseUpload(
        media_stream,
        mimetype=mime_type or "application/octet-stream",
        chunksize=8 * 1024 * 1024,
        resumable=True,
    )
    response = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media,
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
    parser.add_argument("--upload", action="store_true", help="Perform an API upload; default is dry-run only.")
    parser.add_argument("--max-upload-bytes", type=int, default=DEFAULT_MAX_UPLOAD_BYTES,
                        help=f"Maximum local video size accepted (default: {DEFAULT_MAX_UPLOAD_BYTES} bytes). Set explicitly for the available memory budget.")
    parser.add_argument("--owner-approved", action="store_true", help="Additional operator acknowledgement; not identity authentication and not a substitute for the OAuth-bound per-clip approval record.")
    parser.add_argument("--confirm-rights", action="store_true", help="Confirm that the exact local video and all included assets are cleared for this upload.")
    parser.add_argument("--approval-record", type=Path,
                        help="OAuth-bound per-clip approval JSON; required for approval and upload.")
    parser.add_argument("--clip-id", help="Stable clip ID to bind to the approval.")
    parser.add_argument("--source-id", help="Source ID in the source-rights registry.")
    parser.add_argument("--rights-db", type=Path, default=Path("aro_studio_data/source_rights.sqlite3"),
                        help="SQLite source-rights registry.")
    parser.add_argument("--approve-clip", action="store_true",
                        help="Authenticate the channel owner and record explicit approval; does not upload.")
    args = parser.parse_args()

    try:
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        if args.approve_clip and args.upload:
            raise PermissionError("--approve-clip and --upload must be separate invocations")
        video, body = validate_upload(
            args.video, args.rights_report, title=args.title,
            description=args.description, tags=tags, privacy=args.privacy,
            made_for_kids=args.made_for_kids,
            owner_approved=args.owner_approved,
            rights_confirmed=args.confirm_rights,
            upload_requested=args.upload,
            max_upload_bytes=args.max_upload_bytes,
        )
        if args.approve_clip:
            if not args.clip_id or not args.source_id or args.approval_record is None:
                raise PermissionError("--approve-clip requires --clip-id, --source-id and --approval-record")
            approval_report = load_rights_report(args.rights_report)
            if approval_report.get("clip_id") != args.clip_id or approval_report.get("source_id") != args.source_id:
                raise PermissionError("approval clip/source IDs must match the rights report exactly")
            from googleapiclient.discovery import build
            from backend.app.rights_registry import SourceRightsRegistry
            from backend.app.youtube_owner_approval import (
                verify_authenticated_channel_owner, write_owner_approval_record,
            )
            credentials = _authorize_google(
                args.client_secrets.expanduser(), args.token.expanduser()
            )
            youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
            expected_subject = os.environ.get("ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT", "")
            expected_channel = os.environ.get("ARO_YOUTUBE_CHANNEL_ID", "")
            if not expected_subject or not expected_channel:
                raise PermissionError("ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT and ARO_YOUTUBE_CHANNEL_ID must be configured")
            oauth_client_id = _oauth_client_id(args.client_secrets.expanduser())
            owner = verify_authenticated_channel_owner(
                credentials, youtube, oauth_client_id=oauth_client_id,
                expected_google_subject=expected_subject, expected_channel_id=expected_channel,
            )
            approval_rights_registry = SourceRightsRegistry(args.rights_db.expanduser())
            require_report_publish_permissions(
                approval_report, approval_rights_registry, args.source_id
            )
            expected_confirmation = _approval_confirmation_phrase(args.clip_id, args.privacy)
            print(
                "Authenticated channel: " + owner.channel_id + "\n"
                "This records approval for this exact clip and source only. "
                "It does not upload or publish.\n"
                f"Type {expected_confirmation!r} to continue:",
                file=sys.stderr,
            )
            confirmation = input("> ").strip()
            if confirmation != expected_confirmation:
                raise PermissionError("channel-owner approval confirmation did not match")
            record = write_owner_approval_record(
                args.approval_record.expanduser(), clip_id=args.clip_id,
                source_id=args.source_id, video_path=video, owner=owner,
                privacy=args.privacy, confirmed=True,
            )
            print(json.dumps({
                "status": "owner_approval_recorded",
                "upload_performed": False,
                "approval": record,
            }, ensure_ascii=False, indent=2))
            return 0
        if not args.upload:
            print(json.dumps({
                "status": "dry_run_validated",
                "video_file": video.name,
                "metadata": body,
                "upload_performed": False,
                "next_step": "Review metadata and rights, obtain an OAuth-bound approval record, then rerun with --upload --owner-approved --confirm-rights --approval-record if authorized.",
            }, ensure_ascii=False, indent=2))
            return 0
        if args.approval_record is None:
            raise PermissionError("actual upload requires --approval-record")
        if not args.clip_id or not args.source_id:
            raise PermissionError("actual upload requires --clip-id and --source-id")
        upload_report = load_rights_report(args.rights_report)
        if upload_report.get("clip_id") != args.clip_id or upload_report.get("source_id") != args.source_id:
            raise PermissionError("upload clip/source IDs must match the rights report exactly")
        result = upload_video(
            video, body, client_secrets=args.client_secrets.expanduser(),
            token_path=args.token.expanduser(),
            rights_report_path=args.rights_report.expanduser(),
            approval_record_path=args.approval_record.expanduser(),
            rights_db_path=args.rights_db.expanduser(),
            clip_id=args.clip_id,
            source_id=args.source_id,
            owner_approved=args.owner_approved,
            rights_confirmed=args.confirm_rights,
            max_upload_bytes=args.max_upload_bytes,
        )
        print(json.dumps({"status": "uploaded", **result}, indent=2))
        return 0
    except (OSError, ValueError, PermissionError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"YouTube upload stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
