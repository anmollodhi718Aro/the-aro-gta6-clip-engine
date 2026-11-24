# YouTube OAuth Upload Adapter

This optional adapter can stage one locally supplied, authorized video through the official YouTube Data API v3. It uses a loopback desktop OAuth flow. It does not download livestreams, extract other creators' video bytes, or automatically publish content.

**Current live-upload boundary: PRIVATE only.** The implementation rejects unlisted and public upload requests before OAuth/API work. A successful API request is not treated as success unless YouTube's response explicitly confirms PRIVATE visibility.

## 1. Set up Google OAuth locally

1. Create or select a Google Cloud project controlled by or authorized for the destination channel owner.
2. Enable **YouTube Data API v3**.
3. Configure the OAuth consent screen and add test users if the app is in testing mode.
4. Create a **Desktop app** OAuth client.
5. Save the downloaded client JSON locally, for example at `.secrets/client_secret.json`, and pass it with `--client-secrets` if it is not at the CLI default path.
6. Never commit the client JSON, OAuth tokens, destination profile file, or approval records.

Install the optional dependencies:

```bash
pip install -e ".[youtube-upload]"
```

The current OAuth flow requests these scopes:

- `openid`
- `https://www.googleapis.com/auth/youtube.readonly`
- `https://www.googleapis.com/auth/youtube.upload`

The read-only scope is used to resolve the authenticated channel with `channels.list(mine=true)`. Existing token files without the required scopes must be re-authorized. Token persistence uses a same-directory temporary file and atomic replacement, with restrictive permissions where supported; symlink token paths are rejected.

## 2. Configure a destination profile

For multiple destinations, create `.secrets/youtube_destination_profiles.json`. This file contains identity mappings only, not tokens or client secrets:

```json
{
  "profiles": {
    "channel_one": {
      "google_subject": "VERIFIED_GOOGLE_OIDC_SUBJECT",
      "channel_id": "UC_EXACT_VERIFIED_CHANNEL_ID"
    },
    "channel_two": {
      "google_subject": "SECOND_VERIFIED_GOOGLE_OIDC_SUBJECT",
      "channel_id": "UC_SECOND_EXACT_CHANNEL_ID"
    }
  }
}
```

Replace placeholders only after each destination owner has authenticated through that destination's own OAuth session and the exact channel ID has been confirmed through YouTube's `channels.list(mine=true)` response. Never infer channel IDs from public handles.

Security boundaries:

- The profile file must resolve directly inside this checkout's `.secrets/` directory. A similarly named directory elsewhere is not accepted.
- Profile names must be 1–64 letters, numbers, underscores or hyphens.
- Every profile must map to a distinct YouTube channel ID.
- Each profile receives its own token path: `.secrets/tokens/<profile>.json`.
- A caller cannot override a selected profile's token path with `--token`.
- Keep profile data and token files out of Git.

For a single destination without a profile file, the legacy local environment variables `ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT` and `ARO_YOUTUBE_CHANNEL_ID` may be used. Do not paste OAuth secrets, ID tokens, refresh tokens, or private configuration into chat or issue comments.

## 3. Prepare and validate a rights report

Use the local content pack and rights registry:

```bash
python -m backend.app.content_preflight output/gta6_short.json \
  --rights-db aro_studio_data/source_rights.sqlite3 \
  --platform youtube \
  --output output/preflight_report.json
```

The report must be `ready_for_human_review`, target YouTube, contain no blocking errors, and identify the exact `clip_id` and `source_id` used in the approval and upload commands. Metadata in the registry is not legal verification. A human must inspect the underlying permission evidence and all included game, music, visual, guest and other third-party rights. Permission to process a file does not automatically grant permission to publish or monetize it.

## 4. Dry-run metadata (no upload)

```bash
python -m backend.app.youtube_upload /path/to/authorized-clip.mp4 \
  --rights-report output/preflight_report.json \
  --title "THE ARO clip" \
  --not-made-for-kids \
  --privacy private
```

The CLI requires exactly one audience declaration: `--made-for-kids` or `--not-made-for-kids`. Without `--upload`, the command validates local input and metadata only. A dry-run is not an owner approval and does not upload anything.

## 5. Record authenticated PRIVATE approval for one exact clip

First confirm that the primary source and every source-bound asset have current YouTube `publish` grants in the SQLite rights registry. Then authenticate as the correct destination owner and create an approval in a separate, non-uploading invocation:

```bash
python -m backend.app.youtube_upload /path/to/authorized-clip.mp4 \
  --rights-report output/preflight_report.json \
  --title "THE ARO clip" \
  --not-made-for-kids \
  --privacy private \
  --destination-config .secrets/youtube_destination_profiles.json \
  --destination-profile channel_one \
  --clip-id CLIP_ID --source-id SOURCE_ID \
  --rights-db aro_studio_data/source_rights.sqlite3 \
  --approval-record .secrets/approvals/channel_one/CLIP_ID.json \
  --approve-clip
```

If using the legacy single-destination configuration, omit the two destination-profile arguments and configure the expected Google subject and channel ID locally.

The approval flow:

1. Authenticates through the loopback OAuth flow.
2. Verifies the signed Google ID token against the OAuth client ID and accepted Google issuer.
3. Requires the token's stable `sub` to match the configured destination owner.
4. Resolves the destination channel through the same OAuth session's `channels.list(mine=true)` result and requires an exact channel-ID match.
5. Checks the current YouTube `publish` grant for the clip source and each source-bound rights-report asset.
6. Asks the owner to type `APPROVE PRIVATE <clip_id>`.

The durable approval record cannot overwrite an existing record at the same path. It expires after 24 hours by default and binds the Google subject, reviewer/destination channel, clip ID, source ID, PRIVATE visibility, review time, expiry, and SHA-256 of the exact local video bytes. It does not upload.

## 6. Perform a separately approved PRIVATE upload

Only after reviewing the exact finished file, permission evidence, attribution/disclosures, title, description and audience declaration, run a separate command:

```bash
python -m backend.app.youtube_upload /path/to/authorized-clip.mp4 \
  --rights-report output/preflight_report.json \
  --title "THE ARO clip" \
  --description "Original THE ARO commentary and analysis." \
  --tags "GTA6,GTAVI,THEARO" \
  --not-made-for-kids \
  --privacy private \
  --destination-config .secrets/youtube_destination_profiles.json \
  --destination-profile channel_one \
  --clip-id CLIP_ID --source-id SOURCE_ID \
  --rights-db aro_studio_data/source_rights.sqlite3 \
  --approval-record .secrets/approvals/channel_one/CLIP_ID.json \
  --upload --owner-approved --confirm-rights
```

Immediately before `videos.insert`, the uploader re-verifies the OAuth owner/channel identity, the exact approval binding, and current publish permissions for the primary source and all source-bound assets. The `--owner-approved` and `--confirm-rights` flags are additional operator acknowledgements only. Neither flag authenticates identity or replaces the durable approval record.

The CLI reports success only if YouTube's response includes a video ID and explicitly returns `status.privacyStatus == "private"`. If the response omits the status or reports another visibility, the upload state is **UNVERIFIED**. Inspect YouTube Studio before taking any further action.

**Unlisted and public live uploads are not supported by this uploader.** The current approval writer and upload boundary fail closed unless the requested privacy is PRIVATE. Do not interpret a dry-run or an approval record as permission for public publishing.

## Limits and acceptance gates

- The video must already exist locally and be authorized for the intended use.
- The adapter does not download or extract YouTube/Kick livestream video.
- A YouTube API key is not a substitute for the OAuth upload scope.
- OAuth client secrets, refresh tokens, profile maps and approval records must remain local and out of Git.
- The owner must provide the correct made-for-kids declaration; do not guess.
- There is no scheduling or automatic posting.
- Unit tests use synthetic files and mocked Google/YouTube clients. They do not perform network uploads.
- Owner-side OAuth configuration, independent security review, owner-controlled integration, owner-device verification and a separately authorized real-media PRIVATE acceptance test remain outstanding. Hosted CI and synthetic MP4 checks do not satisfy those gates.
- Public publishing remains a separate owner-controlled decision and is not enabled by this uploader.

