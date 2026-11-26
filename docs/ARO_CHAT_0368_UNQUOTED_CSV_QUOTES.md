# ARO-CHAT-0368 | Reject Quotes Inside Unquoted Candidate CSV Fields

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-368
- Parent: PR #387, preserving PR #386's original dependency chain.
- Branch: `workstream/aro-chat-0368-reject-quotes-in-unquoted-candidate-csv-fields-2026-11-26`
- Starting SHA: `9421303689cdcaeddd4f7c58ed1903c810182d56`

## Finding and change

Python's `csv.DictReader(strict=True)` rejects malformed characters after a closing quoted field, but it still accepts a double quote embedded inside an unquoted field. That leaves a malformed candidate row accepted by the strict candidate loader.

Added a streaming quote-boundary validator before `DictReader`. It rejects a quote encountered after an unquoted field has begun, while preserving correctly quoted fields, doubled quote escapes, delimiters, and line breaks inside quoted fields. The validator streams lines and does not load the entire CSV into memory.

Added `tests/test_candidate_csv_unquoted_quote.py`:
- Reject a malformed later row containing a quote inside an unquoted value, even when row 1 was selected.
- Accept a source ID containing a correctly escaped quote inside a quoted CSV field.

Synthetic CSV text only. No media files, FFmpeg/FFprobe, OAuth, credentials, network upload, or publishing were used.

## Verification

- Initial production commit: `6daea742fdc295d95ea84a383af214f7aefb00d6`; newline-handling correction: `66af4d68d7bf739e459deaa5ed7b41f294b6e420`.
- Initial regression test commit: `7da1a42b9e8e57ae6295a391b3491ba73180a7f7`; fixture line-ending correction: `cdca2723dca3c4779d036777d22f59465ece335e`.
- Both corrections were made before final read-back; the current branch head contains the corrected source and test.
- Local unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety and handoff

Keep the continuation draft-only and preserve PR #387 and PR #386 as OPEN / DRAFT / UNMERGED. No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
