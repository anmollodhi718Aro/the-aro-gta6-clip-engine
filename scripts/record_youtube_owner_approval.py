"""Record a short-lived per-clip approval from the OAuth-authenticated channel owner.

This command only records a decision. It never calls the YouTube upload endpoint.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.youtube_upload import _authorize_google, load_rights_report
from backend.app.youtube_owner_approval import (
    require_active_publish_permission,
    verify_authenticated_channel_owner,
    write_owner_approval_record,
    sha256_file,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a durable OAuth-bound approval for one exact local video.")
    parser.add_argument("video", type=Path)
    parser.add_argument("--rights-report", type=Path, required=True)
    parser.add_argument("--clip-id", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--approval-record", type=Path, required=True)
    parser.add_argument("--client-secrets", type=Path, default=Path("client_secret.json"))
    parser.add_argument("--token", type=Path, default=Path("token.json"))
    args = parser.parse_args()

    expected_subject = os.environ.get("ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT", "")
    expected_channel = os.environ.get("ARO_YOUTUBE_CHANNEL_ID", "")
    if not expected_subject or not expected_channel:
        raise SystemExit("Set ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT and ARO_YOUTUBE_CHANNEL_ID first.")

    report = load_rights_report(args.rights_report)
    if report.get("clip_id") != args.clip_id or report.get("source_id") != args.source_id:
        raise SystemExit("Rights report clip/source IDs do not match the requested approval.")
    require_active_publish_permission(report.get("permission_evidence"), args.source_id)

    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise SystemExit('Install optional upload dependencies: pip install -e ".[youtube-upload]"') from exc

    credentials = _authorize_google(args.client_secrets.expanduser(), args.token.expanduser())
    try:
        config = json.loads(args.client_secrets.expanduser().read_text(encoding="utf-8"))
        client_id = config.get("installed", config.get("web", {})).get("client_id")
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        raise SystemExit("OAuth client configuration is unreadable.") from exc
    if not client_id:
        raise SystemExit("OAuth client ID is missing.")
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    owner = verify_authenticated_channel_owner(
        credentials, youtube, oauth_client_id=client_id,
        expected_google_subject=expected_subject, expected_channel_id=expected_channel,
    )
    phrase = f"APPROVE {args.clip_id}"
    print("Authenticated channel owner and destination channel verified.")
    print(f"Clip: {args.clip_id} | Source: {args.source_id} | Video SHA-256: {sha256_file(args.video)}")
    if input(f"Type exactly '{phrase}' to approve this clip for this channel: ").strip() != phrase:
        raise SystemExit("Approval not recorded.")
    record = write_owner_approval_record(
        args.approval_record, clip_id=args.clip_id, source_id=args.source_id,
        video_path=args.video, owner=owner, confirmed=True,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    print(json.dumps({
        "status": "approval_recorded",
        "clip_id": record["clip_id"],
        "source_id": record["source_id"],
        "destination_channel_id": record["destination_channel_id"],
        "expires_at": record["expires_at"],
        "upload_performed": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
