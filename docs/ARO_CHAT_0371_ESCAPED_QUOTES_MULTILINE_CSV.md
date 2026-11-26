# ARO-CHAT-0371 | Escaped Quotes Across Multiline Candidate CSV Fields

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-371
- Branch: `workstream/aro-chat-0371-escaped-quotes-multiline-csv-2026-11-26`
- Base: `workstream/aro-chat-0370-cr-only-candidate-csv-newlines-2026-11-26`
- Parent: PR #390, preserving the candidate-CSV continuation chain to PR #386.

## Scope

Add a synthetic regression proving the strict candidate CSV loader accepts a valid escaped double quote followed by embedded LF and CRLF line breaks inside one quoted optional field. This exercises the lexical state transition from a doubled quote back into a quoted field while physical line iteration continues.

## Change

- Added `tests/test_candidate_csv_escaped_quote_multiline.py`.
- No production code changed.
- No media, FFmpeg/FFprobe, OAuth, credentials, upload, or publishing behavior is touched.

## Validation

- GitHub write acknowledgement: PRESENT for the test file.
- GitHub source read-back: PENDING.
- Local unit test: NOT RUN.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety

Keep the continuation draft-only and unmerged. No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
