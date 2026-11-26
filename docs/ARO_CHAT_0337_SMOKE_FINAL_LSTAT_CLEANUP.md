# ARO-CHAT-0337 — close smoke verifier descriptor when final lstat fails

- Exact chat title: ARO-CHAT-0337 | Close Smoke Verifier Descriptor When Final Lstat Fails.
- Workstream: ARO-GTA-P0-337; continuation of existing draft PR #386 on its original branch and base.
- Starting observed head: `a7e6479a0f97ae60370728820ed976c69171a6e8`.
- Added `test_hash_verified_output_closes_descriptor_when_final_lstat_fails` to `tests/test_synthetic_single_clip_smoke.py`.
- The test allows the initial pathname inspection, opens the output descriptor, completes byte hashing, then injects an `OSError` into the final pathname inspection. It confirms the exception propagates and the descriptor is closed by the helper's `finally` block.
- Test commit: `c9e5dda27cef317402ba402e303aa531f195b671`.
- Production code unchanged. This complements the existing read-failure and initial-`fstat` cleanup regressions by covering failure during the final path-identity check.
- Local unit tests NOT RUN in this connector session. Synthetic FFmpeg end-to-end NOT RUN. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED. Independent review NOT RECORDED. Owner-device Windows verification NOT VERIFIED. Authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and its original base/ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads and public publishing disabled.
