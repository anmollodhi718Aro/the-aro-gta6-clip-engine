# Authorized Live-Source to Owner-Approved Upload Pipeline

## Product flow

1. A creator explicitly grants access through an official platform authorization flow, or supplies a platform-approved media reference under a clear grant.
2. The source registry records creator/source identity, granted scopes, grant time, expiry and revocation state. OAuth tokens must remain in a secure secret store, never Git.
3. A provider adapter discovers live-stream metadata only while the matching creator's `read_live_stream` grant is active.
4. Media bytes are received only through a provider-approved interface or a creator-supplied authorized recording/export. Metadata access is not video ingestion.
5. The existing local renderer processes only media whose editing rights are confirmed for that exact input.
6. Every finished clip enters `needs_review`; the channel owner reviews the preview and metadata.
7. Publishing requires both an immutable per-clip owner approval and a current, independent `publish` permission.

## Permission boundaries

Creator permission authorizes only the granted source scopes. It does not authorize channel publication. Channel-owner approval is a separate per-clip decision. Expired or revoked creator permission blocks further source discovery. The upload gate independently checks publish permission and final owner approval.

## Implemented foundation

- `backend/app/live_sources.py`: provider-neutral adapter contract, timezone-aware stream metadata, matching creator/source grant check before provider access, and provider-response identity validation.
- `backend/app/approval.py`: immutable `needs_review` / `approved` / `rejected` decision model; final decisions cannot be changed in place; upload gate requires active publish scope.
- `tests/test_live_sources_and_approval.py`: synthetic adapter tests for missing, mismatched, expired and revoked source grants; pending/rejected approvals; and independent publishing scope.

## Authenticated local YouTube uploader gate

The optional local uploader now has a fail-closed, OAuth-backed per-clip approval gate:

- Verify the signed Google OIDC ID token's issuer and OAuth-client audience; the token `sub` must match the locally configured `ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT`.
- The same active OAuth credentials are used with the official YouTube Data API `channels.list(mine=True)`. The returned channel ID must match `ARO_YOUTUBE_CHANNEL_ID`; the configured ID is not accepted as proof by itself.
- Run `--approve-clip` as a separate invocation. After identity and current publish-scope checks, the CLI requires typing the exact `APPROVE <clip_id>` phrase. This operation records approval only and never uploads.
- The durable approval record is created atomically without overwriting an existing record. It binds the Google OIDC subject, reviewer/destination channel ID, clip ID, source ID, exact local video SHA-256, timezone-aware review timestamp and expiry (24 hours by default). The file is restricted to the current user where the platform supports file permissions.
- The source-rights SQLite registry independently verifies the exact source's active `publish` scope for YouTube, including validity, expiry and revocation.
- Before the upload request, the uploader rechecks the authenticated channel, exact approval and current rights; it repeats those checks immediately before `videos.insert`. The CLI `--owner-approved` and `--confirm-rights` flags are additional explicit intent checks, never identity authentication.
- Tests use mocked YouTube API clients and temporary SQLite databases. No unit test performs a network upload.

This is a local security gate, not evidence of a completed real upload or production OAuth operations. Configure the expected Google OIDC subject and destination channel ID locally; never commit OAuth client secrets or token files. Owner setup and any real upload remain separate, explicit actions.

## Not production functionality

The repository still does not implement OAuth screens, encrypted token storage, refresh/revocation webhooks, a real live-source provider, creator media-byte ingestion, or a persistent review UI. The optional local YouTube upload adapter is gated as described above and has not been used for a real upload. It does not extract protected stream URLs or bypass platform controls. A real provider integration must use its official supported API and media-access mechanism.

## Next increments

1. Implement the first provider's official OAuth flow and scoped consent.
2. Add encrypted token storage, refresh, expiry and revocation handling.
3. Confirm the provider-supported recording/export handoff for actual media bytes.
4. Persist review records and expose preview/approve/reject operations.
5. Expand owner-side OAuth lifecycle handling and retain current rights/approval rechecks immediately before upload.
6. Default to private staging and require explicit owner confirmation for every public upload.
