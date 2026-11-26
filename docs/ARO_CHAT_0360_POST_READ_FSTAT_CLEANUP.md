# ARO-CHAT-0360 | Close Output Descriptor When Post-Read Fstat Fails

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-360
- Parent: existing draft PR #386; original branch and base preserved.
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`

## Finding

The synthetic output verifier opens a descriptor, hashes the file, then calls `os.fstat` again to confirm that the opened file remained stable. The existing `finally` block should close the descriptor even if this post-read metadata check raises. This regression isolates that failure point from the already-covered initial-fstat and read-failure cases.

## Change

Added `tests/test_synthetic_smoke_post_read_fstat_cleanup.py`. The test allows the initial descriptor metadata check to succeed, injects an `OSError` on the second `os.fstat` call after hashing reaches EOF, and verifies that the error propagates, the descriptor is closed, and the output bytes remain unchanged.

Production code unchanged. Temporary synthetic files only; no FFmpeg/FFprobe process is launched and no media is processed.

## Validation

- GitHub source write/read-back: pending.
- Local unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety

Preserve PR #386 OPEN / DRAFT / UNMERGED and its original ancestry. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
