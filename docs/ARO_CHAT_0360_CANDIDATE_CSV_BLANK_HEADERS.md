# ARO-CHAT-0360: Reject Blank and Duplicate Candidate CSV Headers

- Chat ID: ARO-CHAT-0360
- Workstream: ARO-GTA-P0-360
- Scope: focused regression coverage for the candidate CSV header validation in the existing single-selected-clip workflow.
- Continued on draft PR #386's existing branch and base; no ancestry changes.

## Change

Added `tests/test_candidate_csv_blank_headers.py` with three cases:
- A blank middle header cell.
- A trailing blank header cell, which Python's `csv.DictReader` represents as `None`.
- A duplicate header name.

Each case requires `load_selected_candidate()` to reject the file with the existing fail-closed blank/duplicate-column error. The tests use temporary synthetic CSV text only. No media is opened, rendered, uploaded, or published. Production code is unchanged.

## Evidence and status

- Test commit: `57e097904abab83e44b8405f8434d4b704d06c37`.
- Source write completed through GitHub; test file read-back and execution have not yet been performed in this session.
- Unit tests: NOT RUN.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety

Preserve PR #386 OPEN / DRAFT / UNMERGED and its existing ancestry. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
