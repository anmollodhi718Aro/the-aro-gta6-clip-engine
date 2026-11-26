# ARO-CHAT-0373 | Accept Escaped Quotes and Commas in Candidate CSV Headers

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-373
- Parent: Draft PR #394, based on PR #393. Preserve #394 -> #393 -> #390 -> #389 -> #388 -> #387 -> #386.
- Branch: `workstream/aro-chat-0373-escaped-quoted-csv-header-compat-2026-11-26`
- Starting SHA: `2ee70a2a4deaa8f321bc7f7f4f5f4c626bd2bdc5`
- Scope: one synthetic CSV compatibility regression; production code unchanged.

## Change

Added `tests/test_candidate_csv_escaped_quoted_header.py`. The fixture includes an optional header cell containing both a doubled-quote escape and a comma inside a quoted header cell, plus a data value containing a comma and escaped quotes. It verifies the strict streaming guard and DictReader continue accepting valid CSV quoting while the selected candidate is returned with its expected identity and bounds.

No renderer, media, OAuth, uploader, upload, or publishing behavior changed.

## Validation

- GitHub source write/read-back: PENDING.
- Local unit tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: PENDING / NOT VERIFIED.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.
- P0 pipeline: NOT COMPLETE.

## Safety

Keep this PR OPEN / DRAFT / UNMERGED. No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
