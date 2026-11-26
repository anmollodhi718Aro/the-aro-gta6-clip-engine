# ARO-CHAT-0335 — close synthetic output verifier descriptor on read failure

Date: 2026-11-26

## Change
Added a regression for `scripts.synthetic_single_clip_smoke._hash_verified_output`. The test injects an `OSError` from the low-level read operation after the output file descriptor has been opened. It then verifies that the helper's `finally` path closes that descriptor, demonstrated by `os.fstat()` failing on the captured descriptor.

This protects the smoke verifier's resource lifecycle on exceptional reads. Production code was unchanged because the existing `finally: os.close(descriptor)` already implements the required cleanup.

## Evidence
- Test commit: `33d0ce67bf5f6fb6d86003a3e7953d371b0e1bec`
- Regression source: `tests/test_synthetic_single_clip_smoke.py`
- Active branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Existing PR: #386, preserved OPEN / DRAFT / UNMERGED.

## Verification
- Regression added and source write confirmed through GitHub contents API.
- Local unit tests: NOT RUN.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety boundary
No workflow dispatch/retry, merge, rebase, retarget, credentials, OAuth, real-media processing, upload, publishing, or deployment was performed. Upload and publishing remain disabled. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
