# ARO-CHAT-0369 | Cover Multiline and Unclosed Candidate CSV Quotes

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-369
- Parent: PR #388, stacked on PR #387 and PR #386. Preserve the existing dependency chain.
- Branch: `workstream/aro-chat-0369-csv-multiline-and-unclosed-quote-regressions-2026-11-26`
- Starting SHA: `6e615d6fea146d3284a0c99ff7df918f9129bc3f`

## Scope

Test-only continuation of the strict candidate CSV parser. The prior work added a streaming lexical guard that rejects quote characters inside unquoted fields while preserving valid escaped quotes and quoted newlines. This continuation makes two additional parser boundaries durable repository regressions:

1. A malformed later row with an unterminated quoted field must invalidate the complete CSV even when row 1 was selected.
2. A valid CRLF sequence embedded inside a quoted optional field must remain accepted.

The tests use synthetic CSV text only. Production code, media handling, FFmpeg/FFprobe, OAuth, uploader, and publishing behavior are unchanged.

## Changes

- Added `tests/test_candidate_csv_multiline_and_unclosed_quotes.py`.
- Regression 1 asserts fail-closed handling of an unterminated quote in a later row.
- Regression 2 asserts acceptance of a quoted optional field containing an embedded CRLF line break.

## Validation

- GitHub write acknowledgement: test file commit `c1f5218e46e48d0961be9f7e2e47d221df3c48e5`.
- Local unit tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

Do not transfer predecessor CI results to this new head. No claim of test or pipeline completion is made.

## Safety

Draft-only engineering. Keep PR #388, #387, and #386 OPEN / DRAFT / UNMERGED. No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
