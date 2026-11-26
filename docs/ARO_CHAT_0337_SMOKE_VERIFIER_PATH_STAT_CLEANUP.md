# ARO-CHAT-0337 | Close output verifier descriptor when initial path stat fails

- Chat ID: ARO-CHAT-0337
- Workstream: ARO-GTA-P0-337
- Scope: one focused regression on the existing P0 draft PR #386 branch and original base.
- Added `test_verified_output_hash_closes_descriptor_when_initial_path_stat_fails`. The test allows `os.open()` and the first descriptor `os.fstat()` to succeed, injects an `OSError` from the subsequent pathname `lstat()`, and verifies the opened descriptor is closed by the helper's `finally` block.
- Production code unchanged. This covers a distinct failure point from ARO-CHAT-0335's read failure and ARO-CHAT-0336's initial descriptor-stat failure.
- Test commit: `efb7f74c1fcc3f49ffa4722c7a1cf2b32f888602`.
- Unit tests NOT RUN in this connector session. Synthetic FFmpeg end-to-end NOT RUN. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED. Independent review NOT RECORDED. Owner-device Windows verification NOT VERIFIED. Authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and its original branch/base. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
