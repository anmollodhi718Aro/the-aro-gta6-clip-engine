# Testing Plan

## Test levels

### Unit tests
- timestamp parsing and normalization
- source permission state and scope validation
- rolling chat-rate baseline
- spike detection on synthetic event sequences
- candidate score calculation and explanation
- clip-window bounds and minimum/maximum duration validation
- local renderer rights confirmation, path validation, overwrite protection, timeout, and failure cleanup

### Integration tests
- permitted event adapter to normalized event model
- permission registry to ingestion gate
- event batch to candidate list
- candidate list to human review state
- authorized local asset to review-only MP4 render

### End-to-end tests
Use synthetic events and a short synthetic video generated during CI. Confirm that the renderer exports a playable MP4 of the requested duration and does not publish anything. Separately inspect output quality using a video the user owns or is explicitly authorized to provide.

## Test fixtures

Include:
- normal chat traffic
- a clear synthetic spike
- bursty but irrelevant chat
- delayed and out-of-order events
- duplicate events
- missing timestamps
- expired, revoked, and out-of-scope permissions
- inaccessible or unauthorized media asset
- synthetic video generated at test time, not committed to the repository

Do not include real user tokens, private chat archives, or copyrighted footage without documented permission in fixtures.

## Release gates

- all automated tests pass
- no unresolved critical security findings
- permission checks and manual approval are verified
- error messages do not expose secrets
- backup/restore and deletion behavior are tested before hosted public use
- known limitations are documented

A green CI run only proves the checks that actually ran. It does not prove live-source reliability or production readiness.
