# ARO-CHAT-0323 — smoke harness regression coverage and digest validation

- Workstream: ARO-GTA-P0-323.
- Continued existing draft PR #386 on its existing branch and base.
- Added `tests/test_synthetic_single_clip_smoke.py` to cover missing FFmpeg executable handling, generated-media command composition, the exact selected four-second render interval, rights-confirmed execution, upload/publishing-disabled assertions, temporary artifact cleanup, and rejection of malformed SHA-256 output metadata.
- Tightened `scripts/synthetic_single_clip_smoke.py` so the reported output digest must be exactly 64 lowercase hexadecimal characters, not merely a 64-character string.
- Test commit: `88077f513b6cc9e1fd7bcdfc54a31bc9b8ac5fdd`.
- Production guard commit: `63d73f3c411089e45d9a77d73f0a24b08bfbf8f7`.
- Tests NOT RUN in this connector session. Python source syntax was inspected but no repository runtime is available here. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; no workflow dispatch/retry was performed.
- No real GTA 6 media processed. No upload, publishing, merge, rebase, retarget, or deployment.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and its original ancestry. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
