# Authorized Live-Source to Owner-Approved Upload Pipeline

## Product flow

1. A creator explicitly connects their platform account through the platform's official OAuth/API flow, or supplies a platform-approved media reference under a written grant.
2. The source registry stores creator/source identity, granted scopes, grant time, expiry and revocation state. Tokens belong in a secrets store, never Git.
3. A provider adapter discovers live-stream metadata only while the creator's `read_live_stream` grant is active.
4. The ingestion worker obtains media only through a provider-approved interface/reference. It must not scrape pages, rip streams, defeat DRM, or bypass platform controls.
5. The detector proposes timestamps and creates clips using the existing FFmpeg renderer, only when the grant also permits processing/rendering.
6. Every rendered clip enters `needs_review`. The channel owner reviews the preview, title, description and destination.
7. Publishing is impossible unless the owner explicitly approves that clip and a current `publish` grant exists. Rejection is final for that clip.

## Approval boundary

The owner approval gate is separate from creator source permission. Creator permission allows the specified source processing; it does not silently authorize public uploads. The owner must approve each upload. A revoked/expired creator grant blocks further source reads and processing.

## Provider adapter contract

`backend/app/live_sources.py` defines the provider-neutral contract. Each platform adapter must implement its official OAuth, quota handling, live metadata lookup, revocation handling and platform-compliant media access. A metadata API that does not provide downloadable media is not treated as a media extractor. In that case the creator must provide a supported authorized recording/export workflow.

## Current implementation status

- Implemented: permission-checked provider adapter contract and stream metadata model.
- Implemented: immutable per-clip approval state and hard publish permission gate.
- Tested: synthetic adapter and approval-gate unit tests.
- Not implemented: production OAuth consent screens, encrypted token vault, YouTube/Twitch provider adapters, live media ingest worker, dashboard preview/review UI, or platform upload adapters.
- Not verified: real creator account connection, live stream ingest, rendered source clip, or public upload.

## Required next increments

1. Choose the first provider and implement OAuth using its official developer API.
2. Add encrypted token storage, token refresh, revocation webhooks/polling and audit events.
3. Implement a provider-compliant media acquisition/export path.
4. Add queue persistence and preview UI with approve/reject controls.
5. Add upload adapter that calls the approval gate immediately before publishing.
6. Exercise end-to-end with a creator test account and a creator-authorized stream/recording.
