# ARO-CHAT-0344 | Preserve Structured CLI Failure for Empty Synthetic Output

- Workstream: ARO-GTA-P0-344.
- Continuation target: existing draft PR #386 on its original branch and base.
- Starting observed head: `90f949421569bd7bc2743d5a45480f29eacc10ab`.
- Added `test_main_emits_structured_failure_for_empty_synthetic_output` to `tests/test_synthetic_single_clip_smoke.py`.
- The fake renderer creates a zero-byte MP4 and returns the correct SHA-256 of empty bytes. The test exercises the public CLI `main()` boundary and verifies exit code 1, parseable JSON `FAIL`, the explicit empty-output error, and upload/publishing remaining false.
- This complements ARO-CHAT-0342/0343 lower-level empty-output rejection by checking the operator-facing structured failure path. Production code unchanged.
- Test commit: `9f7287087f8d793eea942436b700477de948a82d`.
- Validation: tests NOT RUN in this connector session; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows verification NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Safety: preserve PR #386 OPEN / DRAFT / UNMERGED and original ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
