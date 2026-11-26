# ARO-CHAT-0343 | Guard Final-Lstat Regression Test Discovery

- Workstream: ARO-GTA-P0-343.
- Continuation target: existing draft PR #386 on `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`; preserve original base and ancestry.
- Finding: the prior ARO-CHAT-0340 correction moved the final-`lstat()` descriptor-cleanup test into the test class, but the ARO-CHAT-0341 AST guard only checked uniqueness of methods that were already direct class members. A future indentation/placement regression could silently make the required test undiscoverable without failing that uniqueness check.
- Change: added an AST regression requiring `test_hash_verified_output_closes_descriptor_when_final_lstat_fails` to appear exactly once as a direct method of `SyntheticSingleClipSmokeTests`.
- Production code and rendering behavior unchanged.
- Test-file commit: `ce4c81a7103c0ec4489a3add15a446f433798701`.
- Static source review only. Unit tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows verification NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
