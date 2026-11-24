# ARO-CHAT-0213 — Windows-safe post-open symlink race regression

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0213
- Workstream ID: ARO-GTA-P1-213
- Branch: `workstream/aro-chat-0213-windows-safe-post-open-race-test-2026-11-24`
- Base: PR #322 head `449f0a96fac2b3eacfb1544bf9bc9a329ad02a94`
- Parent: draft PR #322

## Finding
PR #322's new post-open same-inode symlink regression passed on Ubuntu but failed on hosted Windows. Its test attempted to rename the approval file while the test's opened descriptor remained live. Windows correctly denied the rename with WinError 32, causing one failure and a teardown cleanup error. This was a test portability defect, not evidence that the production pathname check failed.

## Change
- Reworked only the regression test.
- Keep a real descriptor open through the production check.
- Simulate the post-open pathname observation as a symlink via a narrowly scoped `Path.lstat()` test double on the second pathname check.
- Preserve the assertion that the gate rejects a non-regular post-open pathname.
- Avoid filesystem mutation while a Windows file handle is open.
- Production code is unchanged.

## Validation
- Prior parent PR #322 run #45423955539: Ubuntu job succeeded; hosted Windows failed in this regression test (344 tests, 1 failure, 1 error, 2 skipped).
- New branch test/CI: PENDING; no result claimed until this exact branch PR head's Ubuntu and Windows jobs and logs are inspected.
- Local tests: NOT RUN in this connector session.
- Owner-device Windows and real-media acceptance: NOT VERIFIED / NOT USED.

## Safety
Draft-only. No OAuth, credentials/tokens, real media, network upload, publishing, merge, rebase, retarget, deployment, workflow retry/dispatch, or destructive action. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
