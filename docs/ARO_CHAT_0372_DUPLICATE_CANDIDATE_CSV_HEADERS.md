# ARO-CHAT-0372 | Reject Duplicate Candidate CSV Headers

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-372
- Parent: draft PR #393, preserving PR #393 -> #390 -> #389 -> #388 -> #387 -> #386.
- Branch: `workstream/aro-chat-0372-reject-duplicate-candidate-csv-headers-2026-11-26`
- Starting SHA: `30f792d5a9ae2d70d5f68714b2c38705a34e481b`
- Scope: one synthetic regression test; production code unchanged.

## Change

Added `tests/test_candidate_csv_duplicate_headers.py`. It supplies a duplicate `source_id` header and a valid-looking data row, then asserts `load_selected_candidate()` rejects the duplicate column names before DictReader can silently overwrite one source ID with another.

## Validation

- Test source write acknowledged by GitHub; source read-back and final PR head verification pending.
- Local unit tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Synthetic FFmpeg end-to-end: NOT RUN; this test does not invoke media tools.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.
- P0 clipping pipeline: NOT COMPLETE.

## Safety and handoff

Synthetic CSV text only. No production rendering, FFmpeg/FFprobe, OAuth, uploader, real media, upload, or publishing behavior changed or invoked. Keep this PR and all parent PRs OPEN / DRAFT / UNMERGED. No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.