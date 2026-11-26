# ARO-CHAT-0362: Expanded Candidate CSV Header Regression Coverage

- Chat ID: ARO-CHAT-0362
- Workstream: ARO-GTA-P0-362
- Continued on draft PR #386's existing branch/base; no ancestry changes.

## Serial reconciliation

Concurrent work registered ARO-CHAT-0360 for post-read output-descriptor cleanup and ARO-CHAT-0361 for the production blank-header guard plus its initial regression. This continuation is uniquely assigned ARO-CHAT-0362. The provisional ARO-CHAT-0360 report path is retained as a historical alias; no commit history is rewritten.

## Change

Added `tests/test_candidate_csv_blank_headers.py` to expand coverage beyond the existing trailing-empty-header regression:
- Reject a blank middle header cell.
- Reject a trailing blank header cell parsed by `csv.DictReader` as `None`.
- Reject duplicate header names.

Each case requires `load_selected_candidate()` to reject the malformed schema with the existing blank/duplicate-column error. Fixtures are temporary synthetic CSV text only. Production code is unchanged; no media is opened or processed.

## Evidence and status

- Test commit: `57e097904abab83e44b8405f8434d4b704d06c37`.
- GitHub read-back confirms the test file is present.
- Unit tests: NOT RUN.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety

Preserve PR #386 OPEN / DRAFT / UNMERGED and its original ancestry. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
