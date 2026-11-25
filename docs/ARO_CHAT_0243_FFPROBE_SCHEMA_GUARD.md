# ARO-CHAT-0243 | Fail Closed on Malformed FFprobe Metadata

- Date: 2026-11-25
- Workstream: ARO-GTA-P1-243
- Branch: `workstream/aro-chat-0243-single-video-preflight-schema-guard-2026-11-25`
- Base: PR #380 head `2b52a93515db55425be4c8e8d9ec7ea3e3463231`

## Finding
The one-selected-video preflight parsed FFprobe JSON and validated the format duration, but assumed the `streams` member was a list of objects. Valid JSON with `streams: null`, an object, or a list containing null could raise an uncaught TypeError/AttributeError rather than returning the promised fail-closed PASS/FAIL report.

## Changes
- Require FFprobe's JSON root and `format` member to be objects.
- Require `streams` to be a list containing only objects.
- Convert malformed metadata shapes into a deterministic FAIL report using the existing invalid-metadata error.
- Add regression cases for a non-object root, null format, null/object streams, and a null stream entry.
- Preserve one selected path per invocation and all existing no-processing/no-upload/no-publishing flags.

## Validation
- Source and test commits are recorded below.
- Repository unit tests: NOT RUN in this connector session.
- Exact-head Ubuntu/Windows CI: NOT YET VERIFIED.
- No real media was processed; no upload or publishing occurred.

## Commits
- Production: `aef997b5bcceb207c978bbd36d6190c5aafc317f`
- Tests: `626ad1b0bae2bcb80ea792acc50b9859869b77af`

## Workflow conflict
PR #379 introduces multi-file inventory and conflicts with the later owner requirement for one selected video at a time. PR #380 implements one-file preflight but is stacked on #379's branch. Keep both draft/open/unmerged; do not merge or retarget without owner approval.

## Safety
Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled. No workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, merge, rebase, retarget, or deployment.
