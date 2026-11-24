"""Explicitly approved YouTube Data API upload for local authorized videos.

No upload occurs unless --upload, --owner-approved, --confirm-rights, and an
explicit made-for-kids declaration are supplied. Google OAuth dependencies
are optional and are imported only when an upload is requested.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from typing import Any


UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
IDENTITY_SCOPES = ["openid", "https://www.googleapis.com/auth/youtube.readonly", UPLOAD_SCOPE]
DEFAULT_CATEGORY_ID = "20"  # Gaming



def load_destination_profile(config_path: str | Path, profile_name: str) -> dict[str, Any]:
    """Load one non-secret destination identity; OAuth tokens stay in separate local files."""
    if not isinstance(profile_name, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", profile_name):
        raise ValueError("destination profile name must use 1-64 letters, numbers, underscores or hyphens")
    configured_path = Path(config_path).expanduser()
    if configured_path.parent.is_symlink():
        raise PermissionError("destination profile configuration directory must not be a symlink")
    try:
        path = configured_path.resolve(strict=True)
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PermissionError("destination profile configuration is missing or unreadable") from exc
    if path.parent.name != ".secrets":
        raise PermissionError("destination profile configuration must resolve inside the repository .secrets directory")
    profiles = payload.get("profiles") if isinstance(payload, dict) else None
    if not isinstance(profiles, dict) or not profiles:
        raise PermissionError("destination configuration must contain a non-empty profiles object")
    seen_channels: set[str] = set()
    for name, item in profiles.items():
        if not isinstance(name, str) or not isinstance(item, dict):
            raise PermissionError("destination profile entries must be named JSON objects")
        channel_id = item.get("channel_id")
        subject = item.get("google_subject")
        if not isinstance(channel_id, str) or not channel_id.startswith("UC") or len(channel_id) < 10:
            raise PermissionError(f"destination profile {name!r} has an invalid YouTube channel ID")
        if not isinstance(subject, str) or not subject.strip():
            raise PermissionError(f"destination profile {name!r} is missing its Google subject")
        if channel_id in seen_channels:
            raise PermissionError("each destination profile must map to a unique YouTube channel ID")
        seen_channels.add(channel_id)
    selected = profiles.get(profile_name)
    if not isinstance(selected, dict):
        raise PermissionError(f"unknown destination profile: {profile_name}")
    token_path = path.parent / "tokens" / f"{profile_name}.json"
    return {
        "profile": profile_name,
        "google_subject": selected["google_subject"].strip(),
        "channel_id": selected["channel_id"],
        "token_path": token_path,
    }


def resolve_destination_identity(
    *, config_path: Path | None, profile_name: str | None,
    token_override: Path | None,
) -> tuple[str, str, Path]:
    if bool(config_path) != bool(profile_name):
        raise PermissionError("--destination-config and --destination-profile must be supplied together")
    if config_path and profile_name:
        if token_override is not None:
            raise PermissionError("--token cannot override a destination profile's isolated token path")
        profile = load_destination_profile(config_path, profile_name)
        return profile["google_subject"], profile["channel_id"], profile["token_path"]
    subject = os.environ.get("ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT", "").strip()
    channel = os.environ.get("ARO_YOUTUBE_CHANNEL_ID", "").strip()
    if not subject or not channel:
        raise PermissionError(
            "configure --destination-config/--destination-profile or the legacy owner/channel environment variables"
        )
    return subject, channel, (token_override or Path("token.json")).expanduser()


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
    expected_google_subject: str | None = None,
    expected_channel_id: str | None = None,
) -> dict[str, str]:
    # Enforce the private-only boundary before importing optional Google SDKs,
    # reading credentials, or performing any other OAuth/API-related work.
    privacy = body.get("status", {}).get("privacyStatus")
    if privacy != "private":
        raise PermissionError("this uploader only permits PRIVATE staging; public visibility is a separate owner action")
    if owner_approved is not True or rights_confirmed is not True:
        raise PermissionError("actual upload requires --owner-approved and --confirm-rights")

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise RuntimeError(
            'Google upload dependencies are missing. Install with: pip install -e ".[youtube-upload]"'
        ) from exc

    from backend.app.youtube_owner_approval import (
        verify_authenticated_channel_owner,
        require_current_owner_approval,
    )
    from backend.app.rights_registry import SourceRightsRegistry
    expected_subject = (expected_google_subject or os.environ.get("ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT", "")).strip()
    expected_channel = (expected_channel_id or os.environ.get("ARO_YOUTUBE_CHANNEL_ID", "")).strip()
    if not expected_subject or not expected_channel:
        raise PermissionError("a verified destination profile or owner/channel configuration is required")
    oauth_client_id = _oauth_client_id(client_secrets)
    credentials = _authorize_google(client_secrets, token_path)
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    owner = verify_authenticated_channel_owner(
        credentials, youtube, oauth_client_id=oauth_client_id,
        expected_google_subject=expected_subject, expected_channel_id=expected_channel,
    )
    rights_registry = SourceRightsRegistry(rights_db_path.expanduser())
    mime_type, _ = mimetypes.guess_type(video_path.name)
    media = MediaFileUpload(
        str(video_path),
        mimetype=mime_type or "application/octet-stream",
        chunksize=8 * 1024 * 1024,
        resumable=True,
    )
    current_report = load_rights_report(rights_report_path)
    if not isinstance(clip_id, str) or not clip_id.strip():
        raise PermissionError("requested clip_id is required")
    if not isinstance(source_id, str) or not source_id.strip():
        raise PermissionError("requested source_id is required")
    if current_report.get("clip_id") != clip_id or current_report.get("source_id") != source_id:
        raise PermissionError("requested clip/source IDs do not match the rights report")
    require_report_publish_permissions(current_report, rights_registry, source_id)
    require_current_owner_approval(
        approval_record_path, clip_id=clip_id, source_id=source_id,
        video_path=video_path, owner=owner, privacy=privacy,
        rights_registry=rights_registry,
    )
    # Repeat all identity, approval and current-rights checks immediately
    # before the upload API side effect. Any mismatch fails closed.
    owner = verify_authenticated_channel_owner(
        credentials, youtube, oauth_client_id=oauth_client_id,
        expected_google_subject=expected_subject, expected_channel_id=expected_channel,
    )
    require_current_owner_approval(
        approval_record_path, clip_id=clip_id, source_id=source_id,
        video_path=video_path, owner=owner, privacy=privacy,
        rights_registry=rights_registry,
    )
    require_report_publish_permissions(current_report, rights_registry, source_id)
    response = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media,
    ).execute(num_retries=3)
    video_id = str(response.get("id", "")).strip()
    if not video_id:
        raise RuntimeError("YouTube API response did not include a video ID")
    # The request asks YouTube to stage privately. Do not report success unless
    # the API response itself confirms that exact visibility.
    returned_status = response.get("status")
    if not isinstance(returned_status, dict) or returned_status.get("privacyStatus") != "private":
        raise RuntimeError(
            "YouTube did not confirm PRIVATE visibility in the upload response; "
            "treat the upload state as unverified and inspect it in YouTube Studio"
        )
    return {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "privacy_status": "private",
    }


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
    parser.add_argument("--destination-config", type=Path,
                        help="Local JSON destination map; keep it under .secrets and never commit it")
    parser.add_argument("--destination-profile",
                        help="Exact profile name from --destination-config, e.g. aroanmol7")
    parser.add_argument("--token", type=Path, default=None,
                        help="Legacy single-channel token path; unavailable with destination profiles")
    parser.add_argument("--upload", action="store_true", help="Perform an API upload; default is dry-run only.")
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
        expected_subject = expected_channel = None
        token_path = args.token or Path("token.json")
        if args.approve_clip or args.upload:
            expected_subject, expected_channel, token_path = resolve_destination_identity(
                config_path=args.destination_config,
                profile_name=args.destination_profile,
                token_override=args.token,
            )
        video, body = validate_upload(
            args.video, args.rights_report, title=args.title,
            description=args.description, tags=tags, privacy=args.privacy,
            made_for_kids=args.made_for_kids,
            owner_approved=args.owner_approved,
            rights_confirmed=args.confirm_rights,
            upload_requested=args.upload,
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
                args.client_secrets.expanduser(), token_path
            )
            youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
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
            token_path=token_path,
            rights_report_path=args.rights_report.expanduser(),
            approval_record_path=args.approval_record.expanduser(),
            rights_db_path=args.rights_db.expanduser(),
            clip_id=args.clip_id,
            source_id=args.source_id,
            owner_approved=args.owner_approved,
            rights_confirmed=args.confirm_rights,
            expected_google_subject=expected_subject,
            expected_channel_id=expected_channel,
        )
        print(json.dumps({"status": "uploaded", **result}, indent=2))
        return 0
    except (OSError, ValueError, PermissionError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"YouTube upload stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
