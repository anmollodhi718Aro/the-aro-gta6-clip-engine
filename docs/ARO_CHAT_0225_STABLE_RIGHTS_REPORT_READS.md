# ARO-CHAT-0225 — Detect rights-report mutation during reads

Date: 2026-11-24

## Identity and scope
- Chat ID: ARO-CHAT-0225
- Workstream ID: ARO-GTA-P1-225
- Parent: PR #353, secure rights-report file reads
- Branch: `workstream/aro-chat-0225-stable-rights-report-read-2026-11-24`
- Base: PR #353 head `03071572e8b59bf3f150617e26ea7fd49ca57212`
- Scope: ensure bytes read from the verified rights-report descriptor remain stable for the duration of parsing

## Finding
PR #353 verifies that the rights-report path and opened descriptor identify the same regular file before parsing. The descriptor can still refer to a file modified in place while the report is being read. Path/inode checks alone do not detect a concurrent same-inode write during the read.

## Change
- Read the report bytes from the already-verified descriptor.
- Capture descriptor identity, size, modification time and change time before reading.
- Re-check the same descriptor metadata after reading.
- Reject if the descriptor metadata changes or the number of bytes read differs from the original size.
- Decode UTF-8 and parse JSON only after the stability checks pass.
- Preserve existing schema and rights checks; no upload authorization is added or relaxed.

## Regression
- Add a mocked fstat regression that simulates same-inode metadata changing during the read and verifies fail-closed rejection.
- Synthetic local fixture only; no media or network calls.

## Validation
- Parent PR #353 latest-head workflow lookup returned zero associated runs; its exact-head CI is NOT VERIFIED.
- This follow-up's local tests: NOT RUN in this connector session.
- New branch exact-head CI: PENDING.
- Independent security review: NOT RECORDED.

## Safety
Draft only. No OAuth, credentials/tokens, real media, upload, publishing, workflow retry/dispatch, merge, rebase, retarget, deployment, or destructive action. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.


## Test-fixture cleanup — 2026-11-24
- Corrected the regression fixture to obtain its baseline stat through a context-managed file handle, ensuring the fixture descriptor is closed before the test patches fstat.
- Production behavior is unchanged by this test-only correction.
