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

The uploader requests only the `youtube.upload` OAuth scope. On first use, it opens a loopback browser flow at 127.0.0.1 and stores a local token file with restricted permissions where supported.

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

## 4. Perform an explicitly approved upload

Only after reviewing the exact finished file, all source permissions, attribution/disclosures, title, description and audience declaration:

```bash
python -m backend.app.youtube_upload rendered_clips/RUN_ID/clip_001.mp4 \
  --rights-report output/preflight_report.json \
  --title "THE ARO GTA 6 Highlight" \
  --description "Original THE ARO commentary and analysis." \
  --tags "GTA6,GTAVI,THEARO" \
  --privacy private \
  --not-made-for-kids \
  --upload --owner-approved --confirm-rights
```

The default privacy setting is private. Choose unlisted/public only after checking the final video and channel settings. The upload flags are explicit engineering gates; they do not guarantee legal clearance, platform acceptance, copyright safety, or monetization.

## Limits

- The source file must already exist locally and be authorized for this use.
- The adapter never downloads or extracts YouTube or Kick livestream video.
- A YouTube API key is not a substitute for the OAuth upload scope.
- OAuth client secrets and refresh tokens must remain local and out of Git.
- No scheduling or automatic posting is implemented; each upload is a deliberate CLI action.
- The owner must supply the correct made-for-kids declaration. Do not guess.


## Authenticated per-clip owner approval (ARO-CHAT-0039)

The CLI's \`--owner-approved\` switch is only an additional acknowledgement. It is not proof of identity and cannot authorize an upload by itself.

Before an upload can proceed:

1. OAuth must resolve exactly one destination channel using YouTube Data API \`channels.list(part="id", mine=True)\`. The uploader requests the \`youtube.readonly\` scope in addition to \`youtube.upload\`.
2. The durable approval JSON must identify the exact \`clip_id\` and \`source_id\`, have status \`approved\`, and record the authenticated channel ID as \`reviewed_by\`.
3. The separate permission JSON must contain the matching \`source_id\`, an active \`publish\` scope, and timezone-aware grant/expiry/revocation timestamps.
4. The uploader reloads both records and re-checks the authenticated owner identity immediately before calling \`videos.insert\`.
5. Approval creation is a separate invocation and uses exclusive file creation. Existing records cannot be silently overwritten.

Example local approval-recording command:

\`\`\`powershell
python -m backend.app.youtube_upload .\candidate.mp4 --rights-report .\rights-report.json --title "THE ARO clip" --not-made-for-kids --approval-record .\approvals\clip-001.json --clip-id clip-001 --source-id creator-source-001 --expected-channel-id UC_CONFIGURED_CHANNEL --approve-clip
\`\`\`

Example local upload command (still requires the independent permission record and exact matching approval):

\`\`\`powershell
python -m backend.app.youtube_upload .\candidate.mp4 --rights-report .\rights-report.json --title "THE ARO clip" --not-made-for-kids --approval-record .\approvals\clip-001.json --permission-record .\permissions\creator-source-001.json --clip-id clip-001 --source-id creator-source-001 --expected-channel-id UC_CONFIGURED_CHANNEL --upload --owner-approved --confirm-rights
\`\`\`

Keep OAuth tokens and client secrets local. Unit tests mock the YouTube client and do not upload media. A successful local authorization check is not a real-media acceptance or publishing approval.
