# ARO-CHAT-0341: prevent duplicate smoke-test method definitions

- Exact title: ARO-CHAT-0341 | Prevent Duplicate Synthetic Smoke-Test Method Definitions.
- Workstream: ARO-GTA-P0-341.
- Continuation target: existing draft PR #386 and its original branch/base.
- Verified finding: `tests/test_synthetic_single_clip_smoke.py` defined `test_hash_verified_output_closes_descriptor_when_final_fstat_fails` twice in the same class. Python silently replaced the first method with the second during class creation, so one test definition was not independently discoverable.
- Change: removed the redundant duplicate definition and added an AST-based regression asserting that test method names in `SyntheticSingleClipSmokeTests` are unique. No production code or rendering behavior changed.
- Test-file commit: `ef679a607e9a97a1ead6944f6b7720706a86f07c`.
- Static source review only. Unit tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and original base/ancestry. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
