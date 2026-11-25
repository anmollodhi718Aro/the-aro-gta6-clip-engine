# YouTube OAuth Upload Adapter

This is an optional, explicit-approval upload path for a local video file. It uses the official YouTube Data API v3 and a loopback desktop OAuth flow. It does not access other creators' video bytes or download streams.

## 1. Set up Google OAuth locally

1. Create or select a Google Cloud project owned/authorized by the channel owner.
2. Enable **YouTube Data API v3** for that project.
3. Configure the OAuth consent screen and add the appropriate test users if the app is in testing mode.
4. Create an OAuth client with application type **Desktop app**.
5. Download the client JSON and save it locally as `client_secret.json` in the repository root, or pass another path using `--client-secrets`.
6. Do not commit this file. The repository ignores `client_secret*.json`, `token.json`, and local state.

Install the optional uploader dependencies:

```bash
pip install -e ".[youtube-upload]"
```

The uploader requests `youtube.upload`, `youtube.readonly`, `openid`, and `email` scopes. The read-only scope is used to resolve the authenticated channel through `channels.list(mine=true)`; the configured channel ID must match. Existing token files without the required scopes must be re-authorized. On first use, it opens a loopback browser flow at 127.0.0.1 and stores a local token file with restricted permissions where supported.

Set `ARO_YOUTUBE_CHANNEL_ID` locally to the exact destination channel ID. Do not put OAuth secrets, tokens, or this configuration in Git.

## Multi-channel destination profiles

For separate destinations, create a local file at `.secrets/youtube_destination_profiles.json`. This file is ignored by Git because it is stored under `.secrets/`. It contains channel identity mapping only, never OAuth tokens or client secrets:

```json
{
  "profiles": {
    "aroanmol7": {
      "google_subject": "OWNER_ONE_GOOGLE_OIDC_SUB",
      "channel_id": "UC_CHANNEL_ID_FOR_AROANMOL7"
    },
    "the_arro07": {
      "google_subject": "OWNER_TWO_GOOGLE_OIDC_SUB",
      "channel_id": "UC_CHANNEL_ID_FOR_THE_ARRO07"
    }
  }
}
```

Replace every placeholder only after checking the exact channel ID and Google account identity in that channel's own authorized OAuth session. Do not infer a channel ID from its public handle. Profile names must be unique without regard to letter case (to avoid collisions on case-insensitive filesystems), and every profile must map to a distinct YouTube channel ID. Each profile gets its own token file under `.secrets/tokens/<profile>.json`; the CLI refuses a shared-token override when a profile is selected. In profile mode, the approval record is also isolated: `--approval-record` must be stored beneath a directory whose resolved final name exactly matches the selected profile (for example, `local_approvals/aroanmol7/clip-001.json`). This prevents two destination profiles from pointing at the same approval-record directory.

Use one profile per approval and upload invocation:

```bash
python -m backend.app.youtube_upload rendered_clips/RUN_ID/clip_001.mp4 \
  --rights-report output/preflight_report.json \
  --title "THE ARO GTA 6 Highlight" \
  --not-made-for-kids \
  --destination-config .secrets/youtube_destination_profiles.json \
  --destination-profile aroanmol7 \
  --clip-id clip-001 --source-id source-001 \
  --approval-record local_approvals/aroanmol7/clip-001.json \
  --rights-db aro_studio_data/source_rights.sqlite3 \
  --approve-clip
```

Repeat with `--destination-profile the_arro07` and a different approval-record path only after that destination's owner identity and rights are independently verified. The approval record itself binds the authenticated channel ID and exact video hash, so one profile's approval cannot authorize the other profile. The profile mechanism does not itself prove control of a handle; OAuth verification remains mandatory.

## 2. Create a rights preflight report

Use a structured content pack and the same local rights database used by THE ARO Studio:

```bash
python -m backend.app.content_preflight output/gta6_short.json \
  --rights-db aro_studio_data/source_rights.sqlite3 \
  --platform youtube \
  --output output/preflight_report.json
```

A report must be `ready_for_human_review` and contain no blocking errors. This checks stored permission metadata only; the channel owner must still verify the underlying evidence and all embedded rights.

## 3. Dry-run upload metadata (default)

```bash
python -m backend.app.youtube_upload rendered_clips/RUN_ID/clip_001.mp4 \
  --rights-report output/preflight_report.json \
  --title "THE ARO GTA 6 Highlight" \
  --description "Original THE ARO commentary and analysis." \
  --tags "GTA6,GTAVI,THEARO" \
  --privacy private \
  --not-made-for-kids
```

No API upload occurs unless `--upload` is supplied. The uploader requires an explicit audience declaration using exactly one of `--made-for-kids` or `--not-made-for-kids`.

## 4. Record authenticated owner approval for the exact clip

First ensure the source has an active YouTube `publish` grant in the SQLite rights database. The rights report must include the exact `clip_id` and `source_id`. Authenticate as the configured channel owner and explicitly approve the exact local file in a separate, non-uploading invocation:

```bash
python -m backend.app.youtube_upload rendered_clips/RUN_ID/clip_001.mp4 \
  --rights-report output/preflight_report.json \
  --title "THE ARO GTA 6 Highlight" \
  --not-made-for-kids \
  --clip-id clip-001 --source-id source-001 \
  --rights-db aro_studio_data/source_rights.sqlite3 \
  --approval-record local_approvals/clip-001.json \
  --approve-clip
```

Set `ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT` to the expected Google OIDC `sub` and `ARO_YOUTUBE_CHANNEL_ID` to the destination channel ID in local environment configuration. This step verifies the signed Google ID token's issuer and OAuth-client audience, matches the OIDC subject to the configured owner subject, verifies the same OAuth session's channel through `channels.list(mine=true)`, and checks current source publish permission. For private approval, type `APPROVE PRIVATE <clip_id>`; for unlisted approval, type `APPROVE UNLISTED <clip_id>`; public approval requires the distinct phrase `PUBLISH PUBLIC <clip_id>`. The 24-hour record binds the Google subject, channel ID, clip/source IDs, requested privacy level and exact file SHA-256. It does not upload. Existing approval files are never overwritten.

## 5. Perform the separately requested upload

Only after reviewing the exact finished file, all source permissions, attribution/disclosures, title, description and audience declaration:

```bash
python -m backend.app.youtube_upload rendered_clips/RUN_ID/clip_001.mp4 \
  --rights-report output/preflight_report.json \
  --title "THE ARO GTA 6 Highlight" \
  --description "Original THE ARO commentary and analysis." \
  --tags "GTA6,GTAVI,THEARO" \
  --privacy private \
  --not-made-for-kids \
  --clip-id clip-001 --source-id source-001 \
  --rights-db aro_studio_data/source_rights.sqlite3 \
  --approval-record local_approvals/clip-001.json \
  --upload --owner-approved --confirm-rights
```

Immediately before `videos.insert`, the uploader re-verifies the Google OIDC subject and authenticated channel, the exact account/channel/clip/source/file/privacy approval and current publish permissions for every source-bound asset. The default privacy setting is private. Public or unlisted uploads still require every gate to pass. The `--owner-approved` flag is only an additional operator acknowledgement, never identity authentication or a substitute for the durable record. The flags do not guarantee legal clearance, platform acceptance, copyright safety, or monetization.

## Limits

- The source file must already exist locally and be authorized for this use.
- The adapter never downloads or extracts YouTube or Kick livestream video.
- A YouTube API key is not a substitute for the OAuth upload scope.
- OAuth client secrets and refresh tokens must remain local and out of Git.
- No scheduling or automatic posting is implemented; each upload is a deliberate CLI action.
- The owner must supply the correct made-for-kids declaration. Do not guess.


## Approval binding and privacy rules

- The OAuth ID token is verified against the configured OAuth client ID; its stable Google subject must equal ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT.
- The same OAuth session must resolve the configured destination channel through YouTube channels.list(mine=True).
- Approval records bind both the Google subject and YouTube channel, plus clip ID, source ID, exact local file SHA-256, privacy, review time and expiry.
- A private or unlisted approval cannot authorize a public upload. Public approval requires the distinct phrase PUBLISH PUBLIC CLIP_ID.
- Immediately before videos.insert, the uploader rechecks the current publish grant for the clip source and every source-bound asset in the rights report.
- Tests use synthetic files and mocked YouTube/OAuth clients only. They never perform a real upload.


## Post-upload PRIVATE response verification

The upload CLI reports success only when the official `videos.insert(part="snippet,status")` response contains a video ID and `status.privacyStatus == "private"`. If the response omits the status or reports any other visibility, the command exits as unverified and instructs the operator to inspect YouTube Studio. A request body asking for PRIVATE is not, by itself, evidence that YouTube accepted that visibility. Unit tests cover both confirmed-private and unexpected-visibility responses; tests do not upload to YouTube.


## Windows OAuth token ACL enforcement

On Windows, token persistence disables inherited ACLs on the profile token directory and the temporary token file, grants full control only to the current process user's SID, and reads the resulting ACL back with icacls. Persistence fails closed unless the read-back contains exactly that one full-control ACE. The temporary file receives its restricted ACL before token bytes are written; atomic replacement preserves that file's ACL. The token directory is also restricted so other principals cannot replace profile token files through the directory. On non-Windows platforms, token files retain mode 0600.

This is an application-level ACL check, not a substitute for owner-device verification. Confirm the actual Windows account, filesystem, effective ACL behavior, and token-directory access on the owner's device before enabling OAuth. If whoami or icacls is unavailable, fails, or returns an unexpected ACL, token persistence is rejected. No live OAuth or upload is performed by the regression tests.

Existing Windows token files are checked before credentials are loaded: the profile token directory and token file must both pass the same owner-only ACL read-back. A legacy token with additional explicit principals is rejected rather than read or silently trusted. This prevents the stricter write path from leaving an older, broadly accessible token usable.
