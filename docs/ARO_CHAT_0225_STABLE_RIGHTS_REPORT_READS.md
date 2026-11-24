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


## Bounded-input follow-up — 2026-11-24
- Review identified that a regular-file rights report could still be arbitrarily large, causing an unbounded allocation during the final pre-upload read.
- Added MAX_RIGHTS_REPORT_BYTES = 1 MiB; reject a larger descriptor size before reading and cap the read to limit + 1 bytes so concurrent growth remains bounded.
- Added a synthetic oversized-report regression. Existing descriptor identity, before/after metadata, byte-count, UTF-8 and JSON checks remain in place.
- Production commit: 0a0d22e57b3016b0e3bbacec29c71999086045eb. Test commit: 036ada61be8b5e2c03cbfd24e18ff4eeef96a996.
- Local tests NOT RUN in this connector session. Verify fresh exact-head Ubuntu and hosted-Windows CI; independent security review remains NOT RECORDED.
- Draft only. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. No OAuth, credentials, real media, upload, publishing, workflow retry/dispatch, merge, rebase, retarget, deployment or destructive action.


## Additional regression — truncated descriptor read
- Added a test that simulates a short read while descriptor metadata remains unchanged.
- The test verifies the independent byte-count guard rejects the incomplete payload before UTF-8 decoding or JSON parsing.
- Test commit: `8143da93904b5ed8d6ba8a18a8fb02ebdf471bbb`.
- Local tests NOT RUN in this connector session; exact-head Ubuntu/hosted-Windows CI must be checked for the new branch head. No test result is inferred.
