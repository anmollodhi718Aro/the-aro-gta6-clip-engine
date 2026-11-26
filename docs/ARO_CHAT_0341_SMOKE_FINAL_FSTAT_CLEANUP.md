# ARO-CHAT-0341 | Close smoke verifier descriptor when final fstat fails

- Exact chat title: `ARO-CHAT-0341 | Close Smoke Verifier Descriptor When Final Fstat Fails`.
- Chat ID: ARO-CHAT-0341.
- Workstream: ARO-GTA-P0-341.
- Continued the existing P0 draft PR #386 on its original branch and base: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`.
- Starting observed branch head: `bac9be9e34c2ed62c4e492791c0ce5edec2a2bf6`.
- Added `test_hash_verified_output_closes_descriptor_when_final_fstat_fails` in `tests/test_synthetic_single_clip_smoke.py`.
- The regression lets the initial descriptor `fstat()` succeed, then injects an `OSError` from the final descriptor `fstat()` after the file has been read. It verifies the exception propagates and a subsequent real `fstat()` on the captured descriptor fails, proving the helper's `finally` block closed it.
- Production code unchanged; this exercises a distinct cleanup path from read failure, initial descriptor-stat failure, pathname-stat failures, and premature EOF.
- Test commit: `8147d5e0ad702b2f11aee7cd1764369053b45a9c`.
- Source edit is IMPLEMENTED. Local unit tests NOT RUN in this connector session; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows verification NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and its original branch/base. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
