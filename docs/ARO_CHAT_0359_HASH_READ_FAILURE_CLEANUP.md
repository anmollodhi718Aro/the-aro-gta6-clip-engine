# ARO-CHAT-0359 | Close Output Descriptor When Hash Read Fails

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-359
- Parent: existing draft PR #386; original branch and base preserved.
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`

## Finding

The output hash verifier closes its file descriptor in a `finally` block. Existing regressions cover failures during descriptor metadata checks and pathname identity checks. This focused test covers the separate case where the descriptor read itself raises an `OSError`.

## Change

Added `tests/test_synthetic_smoke_read_failure_cleanup.py`. The test captures the descriptor opened by `_hash_verified_output`, injects an `OSError` from `os.read`, and verifies that the error propagates, the descriptor is closed, and the output bytes remain unchanged.

Production code unchanged. Temporary synthetic files only; no FFmpeg/FFprobe process is launched and no media is processed.

## Commit

- Regression test commit: `f58ef01378b8b1fa8847c1ab653efa483d2456c1`
- Test file: `tests/test_synthetic_smoke_read_failure_cleanup.py`

## Validation

- GitHub source write: PRESENT.
- Local unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety

Preserve PR #386 OPEN / DRAFT / UNMERGED and its original ancestry. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
