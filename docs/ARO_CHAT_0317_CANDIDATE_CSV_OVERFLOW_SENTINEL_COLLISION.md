# ARO-CHAT-0317: isolate candidate CSV overflow sentinel

- Workstream: ARO-GTA-P1-317
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Continued existing draft PR #386 on `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`; no new branch or PR.

## Finding

The strict candidate CSV parser used the literal string `__aro_extra_fields__` as `csv.DictReader.restkey`. A valid input file could contain that same header name as an ordinary user column. DictReader then reused the same dictionary key for user data and overflow cells, causing a valid row to be rejected as if it had extra values.

## Change

- Replace the string restkey with a unique object key for each parser invocation.
- Preserve strict parsing, full-file validation, missing-cell rejection, and extra-cell rejection.
- Add regression coverage proving the reserved-looking header is accepted as ordinary data and genuinely overlong rows are still rejected.

## Validation

- Production and regression commits are recorded in this PR branch.
- Tests were NOT run in this connector session.
- Exact-head Ubuntu/hosted-Windows CI is NOT VERIFIED.
- Independent review and owner-device Windows verification are NOT RECORDED.
- No authorized real MP4 was processed.

## Safety

PR #386 remains OPEN / DRAFT / UNMERGED with its existing base and ancestry. No workflow retry/dispatch, merge, rebase, retarget, real media, OAuth, credentials, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
