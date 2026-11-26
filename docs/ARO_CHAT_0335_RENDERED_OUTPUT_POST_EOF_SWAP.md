# ARO-CHAT-0335 — reject rendered-output replacement after EOF

Date: 2026-11-26

## Scope
Continue the existing P0 single-selected-clip workstream on draft PR #386 and its original branch/base. This task adds a narrowly scoped regression for the final pathname identity check in `_sha256_verified_regular_file`.

## Change
Added `test_verified_output_hash_rejects_path_replacement_after_eof` to `tests/test_single_clip_render.py`. The test wraps the real descriptor read, waits until EOF has been observed, then replaces the output pathname with a different regular file before the verifier performs its final path-stat check. The verifier must raise the existing changed-during-verification error. The test also confirms the original bytes remain at the preserved path and replacement bytes remain at the output path.

This complements ARO-CHAT-0333's pre-hash/open-time replacement test by exercising the distinct post-read/final-path-check window. Production code unchanged.

## Evidence and limits
- Test source committed: `0dc0e1836fdebd0331f534cda5797b89a59e8f2c`.
- Source/test read-back is required before treating this task as implemented.
- Unit tests NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end NOT RUN.
- Exact-head Ubuntu/Windows CI NOT VERIFIED; no workflow was dispatched or retried.
- Independent review NOT RECORDED.
- Authorized real GTA 6 MP4 NOT PROCESSED; owner media/permission handoff remains the acceptance blocker.

## Guardrails
Keep PR #386 OPEN / DRAFT / UNMERGED and preserve its original branch/base/ancestry. No merge, rebase, retarget, workflow dispatch/retry, credentials, real media ingestion, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
