# Testing Plan

## Test levels

### Unit tests
- timestamp parsing and normalization
- source permission state and scope validation
- rolling chat-rate baseline
- spike detection on synthetic event sequences
- candidate score calculation and explanation
- clip-window bounds and minimum/maximum duration validation

### Integration tests
- permitted event adapter to normalized event model
- permission registry to ingestion gate
- event batch to candidate list
- candidate list to human review state
- authorized asset check to render-job request

### End-to-end tests
Use synthetic events and a short, owned or explicitly authorized sample video. Confirm that the workflow creates a candidate clip plan and does not publish anything.

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

Do not include real user tokens, private chat archives, or copyrighted footage without documented permission in fixtures.

## Release gates

- all automated tests pass
- no unresolved critical security findings
- permission checks and manual approval are verified
- error messages do not expose secrets
- backup/restore and deletion behavior are tested before hosted public use
- known limitations are documented

A green CI run only proves the checks that actually ran. It does not prove live-source reliability or production readiness.
