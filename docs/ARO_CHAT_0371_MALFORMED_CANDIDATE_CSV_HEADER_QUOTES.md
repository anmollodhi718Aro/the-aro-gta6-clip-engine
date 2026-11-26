# ARO-CHAT-0371 | Reject Malformed Candidate CSV Header Quotes

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-371
- Parent: PR #390, preserving the existing PR #390 -> #389 -> #388 -> #387 -> #386 dependency chain.
- Branch: `workstream/aro-chat-0371-reject-malformed-candidate-csv-headers-2026-11-26`
- Starting SHA: `d2146334143aeae7372bdbeb43e681ec4a1de816`
- Scope: synthetic regression tests only; production code unchanged.

## Finding and change

The strict streaming CSV quote guard is applied to the complete file, including the header, but the repository did not yet have focused regression tests for malformed quote boundaries in header cells.

Added `tests/test_candidate_csv_malformed_header_quotes.py` with two synthetic cases:
1. Reject a quote embedded after an unquoted header-cell value has begun.
2. Reject non-delimiter text immediately after a closing quote in a quoted header cell.

Both cases provide an otherwise valid required header/data row so the malformed header is the reason the selected candidate must fail closed.

## Validation

- GitHub test-file write acknowledged at commit `513cb96a127113304f35abc78bb2eb9d9c4183b3`.
- Source read-back: PENDING.
- Local unit tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: PENDING / NOT VERIFIED.
- Synthetic FFmpeg end-to-end: NOT RUN; this test does not invoke media tools.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.
- P0 clipping pipeline: NOT COMPLETE.

## Safety and handoff

Test-only synthetic CSV text. Production rendering, FFmpeg/FFprobe, OAuth, uploader, and publishing behavior are unchanged. Keep this PR and parent PRs OPEN / DRAFT / UNMERGED. No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
