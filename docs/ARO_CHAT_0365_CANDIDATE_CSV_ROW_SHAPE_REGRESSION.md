# ARO-CHAT-0365 | Reject Malformed Candidate CSV Rows After Selection

- Chat ID: ARO-CHAT-0365
- Exact chat title: ARO-CHAT-0365 | Reject Malformed Candidate CSV Rows After Selection
- Workstream ID: ARO-GTA-P0-365
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Continuation: existing draft PR #386, original branch and base preserved.
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Scope: test-only regression coverage for full-file candidate CSV validation.

## Change
Added `tests/test_candidate_csv_row_shape.py` with three synthetic CSV regressions. Each selects a valid first row but requires the loader to reject a malformed later row:
- A short later row missing a required value.
- A later row containing more values than the header.
- An unterminated quoted field in a later row.

This protects the existing contract that the complete candidate CSV is parsed and validated before returning the selected candidate. No production code changed. Fixtures contain metadata strings only; no media file is opened and no FFmpeg/FFprobe process is launched.

## Commits
- Test commit: `328574188c9fe8c8e938324bf7e2680c7e59b635`
- Canonical report commit: recorded by this report file's GitHub commit.
- The provisional `docs/ARO_CHAT_0363_CANDIDATE_CSV_ROW_SHAPE_REGRESSION.md` is retained as a historical serial-collision alias. Concurrent registry entries had already reserved 0363 and 0364, so this workstream is uniquely reconciled to ARO-CHAT-0365. No commit history was rewritten.

## Validation status
- GitHub source write: completed.
- Local unit tests: NOT RUN.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety
Keep PR #386 OPEN / DRAFT / UNMERGED and preserve its original ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
