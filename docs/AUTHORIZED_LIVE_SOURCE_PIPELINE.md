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

## Not production functionality

This foundation does not implement OAuth screens, encrypted token storage, refresh/revocation webhooks, a real YouTube provider, video ingestion, durable review storage/UI, or an upload adapter. It does not extract protected stream URLs or bypass platform controls. A real provider integration must use its official supported API and media-access mechanism.

## Next increments

1. Implement the first provider's official OAuth flow and scoped consent.
2. Add encrypted token storage, refresh, expiry and revocation handling.
3. Confirm the provider-supported recording/export handoff for actual media bytes.
4. Persist review records and expose preview/approve/reject operations.
5. Re-check creator permission and destination-channel permission immediately before upload.
6. Default to private staging and require explicit owner confirmation for every public upload.


## Authenticated owner identity requirement

The upload approval contract now requires an explicit owner_identity when calling require_upload_approval. The supplied identity must be a stable subject from a trusted, server-side authenticated channel-owner session. It must match the identity recorded in UploadApproval.reviewed_by.

Do not pass a display name, client-supplied form value, or unverified reviewer string as owner_identity. The helper performs an identity equality check; it does not authenticate users or create a secure session. A future OAuth/session integration must derive the owner subject from verified provider credentials and pass it from the server side. Until that integration exists, the approval foundation is not a production authentication system and no production uploader should rely on it alone.


## Existing YouTube upload CLI integration status

The repository also contains an optional local YouTube uploader in backend/app/youtube_upload.py. That command currently uses explicit --owner-approved and --confirm-rights flags. It does not yet call require_upload_approval or verify the reviewer against the OAuth-authenticated channel identity.

Consequently, the owner_identity check added in this workstream hardens the approval helper contract only. It does not retrofit authenticated owner identity into the existing uploader. Keep public uploads disabled until a separate integration change obtains the authenticated channel subject from the OAuth session, binds it to a durable per-clip approval record, and re-checks the identity and permission immediately before the upload API call. A CLI flag alone is a manual attestation, not identity authentication.
