# Testing Plan

## Unit tests
- timezone-aware permission and event parsing
- source identity and permission-evidence reference validation
- atomic registry persistence, duplicate-source rejection, expiry and revocation
- event source/scope validation, UTC normalization, batch/text bounds, sorting and deduplication
- deterministic spike detection, stable candidate IDs, score and explanation
- immutable review decisions and duplicate-decision rejection
- render rights attestation, active edit_media permission, path validation, overwrite protection, timeout and cleanup

## Integration tests
- registry to event-ingestion permission gate
- normalized events to candidate list
- candidate list to append-only review ledger
- registry edit_media scope to local renderer
- synthetic moving MP4 render and FFprobe duration verification

## End-to-end and acceptance
CI uses synthetic event data and a generated moving pattern. It must not upload or publish. Real-media acceptance is separate and requires owner-authorized media, documented permission for the exact asset, FFprobe inspection, playback, and human acceptance.

## Fixtures
Normal traffic, spikes, out-of-order events, duplicate/conflicting IDs, missing timestamps, oversized batches/text, expired/revoked/out-of-scope permissions, corrupt registries, duplicate review decisions, unauthorized media, and synthetic video generated during CI.

Never include real credentials, private chat archives, or copyrighted footage without documented permission.

## Release gates
- exact-head automated tests pass
- no unresolved critical security findings
- source permissions and human review are verified
- errors do not expose secrets
- backup/restore and deletion behavior are tested before hosted public use
- live ingestion, OAuth upload, publishing, deployment, and public release remain separate gated milestones

Green CI does not prove live-source reliability, owner-device behavior, real-media quality, or production readiness.
