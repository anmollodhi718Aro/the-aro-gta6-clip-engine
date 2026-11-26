# ARO-CHAT-0370 | Accept CR-Only Candidate CSV Newlines

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-370
- Parent: PR #389, preserving the existing #389 -> #388 -> #387 -> #386 dependency chain.
- Branch: `workstream/aro-chat-0370-cr-only-candidate-csv-newlines-2026-11-26`
- Scope: focused regression test only; production code unchanged.

## Change

Added `tests/test_candidate_csv_carriage_return_newlines.py`. The synthetic fixture uses CR-only record separators and a CR embedded inside a properly quoted optional field. The selected candidate must still parse successfully.

This extends the existing CSV compatibility coverage beyond LF and CRLF while exercising the streaming lexical guard across physical text lines. No media files or tools are used.

## Validation

- GitHub source write/read-back: pending at initial submission.
- Local unit tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety

Keep this PR OPEN / DRAFT / UNMERGED. Preserve all parent PRs and ancestry. No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
