"""One-time local OAuth setup for a PRIVATE YouTube destination profile.

Run from the repository root. OAuth tokens and destination identity stay under
.gitignored .secrets/ and are never printed or committed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


def _atomic_private_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise PermissionError("secrets directory must not be a symlink")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Refuse to replace an existing destination map. It may contain another
        # channel profile that must be preserved and reviewed explicitly.
        if path.exists():
            raise FileExistsError(f"{path} already exists; add the profile manually after review")
        os.link(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def setup_destination(
    *, repository_root: Path, client_secrets: Path, profile_name: str,
    selected_channel_id: str | None = None,
) -> dict[str, str]:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", profile_name):
        raise ValueError("profile name must use 1-64 letters, numbers, underscores or hyphens")
    root = repository_root.resolve(strict=True)
    secrets_dir = root / ".secrets"
    if secrets_dir.is_symlink():
        raise PermissionError(".secrets must not be a symlink")
    secrets_dir.mkdir(mode=0o700, exist_ok=True)
    if secrets_dir.resolve(strict=True) != secrets_dir:
        raise PermissionError(".secrets must resolve inside the repository")
    config_path = secrets_dir / "destination_profiles.json"
    if config_path.is_symlink():
        raise PermissionError("destination profile configuration must not be a symlink")
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(config, dict) or not isinstance(config.get("profiles"), dict):
            raise ValueError("existing destination profile configuration is malformed")
    else:
        config = {"profiles": {}}
    profiles = config["profiles"]
    if any(name.casefold() == profile_name.casefold() for name in profiles):
        raise ValueError("a destination profile with this name already exists")

    from backend.app.youtube_upload import (
        IDENTITY_SCOPES, UPLOAD_SCOPE, _authorize_google, _oauth_client_id,
    )
    from backend.app.youtube_owner_approval import _verify_google_id_token

    token_dir = secrets_dir / "tokens"
    if token_dir.is_symlink():
        raise PermissionError("OAuth token directory must not be a symlink")
    token_path = token_dir / f"{profile_name}.json"
    credentials = _authorize_google(client_secrets.expanduser(), token_path)
    claims = _verify_google_id_token(credentials, _oauth_client_id(client_secrets))
    subject = claims.get("sub")
    issuer = claims.get("iss")
    authorized_party = claims.get("azp")
    client_id = _oauth_client_id(client_secrets)
    if (
        not isinstance(subject, str) or not subject.strip()
        or issuer not in ("accounts.google.com", "https://accounts.google.com")
        or (authorized_party is not None and authorized_party != client_id)
    ):
        raise PermissionError("verified Google identity is missing a valid subject, issuer or authorized party")
    if not credentials.has_scopes(IDENTITY_SCOPES) or UPLOAD_SCOPE not in credentials.scopes:
        raise PermissionError("OAuth session is missing required YouTube upload and identity scopes")

    from googleapiclient.discovery import build
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    response = youtube.channels().list(part="id", mine=True).execute()
    items = response.get("items", []) if isinstance(response, dict) else []
    channel_ids = sorted({
        item["id"] for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
        and item["id"].startswith("UC")
    })
    if not channel_ids:
        raise PermissionError("the authenticated Google account has no accessible YouTube channel")
    if selected_channel_id is None:
        if len(channel_ids) != 1:
            raise PermissionError(
                "multiple channels are available; rerun with --channel-id set to one listed channel"
            )
        selected_channel_id = channel_ids[0]
    if selected_channel_id not in channel_ids:
        raise PermissionError("--channel-id is not returned by the authenticated YouTube account")

    if any(
        isinstance(item, dict) and item.get("channel_id") == selected_channel_id
        for item in profiles.values()
    ):
        raise ValueError("this YouTube channel is already assigned to another destination profile")
    profiles[profile_name] = {
        "google_subject": subject,
        "channel_id": selected_channel_id,
    }
    _atomic_private_json(config_path, config)
    return {
        "profile": profile_name,
        "channel_id": selected_channel_id,
        "config_path": str(config_path),
        "token_path": str(token_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Authorize one YouTube channel and create a local PRIVATE-upload destination profile."
    )
    parser.add_argument("--client-secrets", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--channel-id", help="Required only when the Google account exposes multiple channels.")
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        result = setup_destination(
            repository_root=args.repository_root,
            client_secrets=args.client_secrets,
            profile_name=args.profile,
            selected_channel_id=args.channel_id,
        )
        print(json.dumps({"status": "destination_profile_created", **result}, indent=2))
        print("OAuth token and destination map remain local under .secrets/. Do not commit them.")
        return 0
    except (OSError, ValueError, PermissionError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"YouTube destination setup stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
