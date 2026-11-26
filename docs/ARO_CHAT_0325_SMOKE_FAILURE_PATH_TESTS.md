# ARO-CHAT-0325 — synthetic smoke failure-path regression coverage

- Workstream: ARO-GTA-P0-325; continued existing draft PR #386 on its original branch/base.
- Extended `tests/test_synthetic_single_clip_smoke.py` with regression coverage for missing FFprobe (must stop before fixture generation), CLI structured JSON failure when FFmpeg is unavailable, and FFmpeg fixture-generation failure (must not report PASS).
- This complements ARO-CHAT-0324's independent output-byte SHA-256 comparison and mismatch regression.
- Test commit: `7bb0046c805da205abbbe0d1e3ebfeee1982f5f8`.
- Tests NOT RUN in this connector session. Synthetic FFmpeg end-to-end execution NOT RUN. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; no workflow dispatch/retry. Independent review NOT RECORDED. Authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and original base/ancestry. No merge, rebase, retarget, workflow retry/dispatch, OAuth, credentials, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
