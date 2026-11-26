# ARO-CHAT-0312 — strict candidate CSV parsing

Date: 2026-11-26

## Scope

Continue the existing one-selected-video / one-selected-clip pipeline on draft PR #386. Harden the candidate CSV boundary without changing selection semantics or processing any media.

## Finding

Python's default `csv.DictReader` is permissive. It can accept malformed quoting unless strict mode is enabled, places excess cells under the `None` key by default, and fills short rows with `None`. The prior loader also stopped parsing immediately after the selected row, so malformed trailing rows could be ignored.

## Changes

- Enable `strict=True` for CSV parsing.
- Use an explicit overflow key and reject rows with extra cells.
- Reject missing required cells in every data row.
- Parse the complete CSV before accepting the selected row, so malformed trailing content is not ignored.
- Preserve UTF-8 BOM support and one-based explicit row selection.
- Add regressions for malformed quoting after the selected row, extra cells, and missing required cells.
- Update the single-clip operator guide.

## Commits

- Production: `341140bce254c2bd46b1e495222231f5f14fe099`
- Tests: `58f1e342a918c3d1c459c671a6ac459ea94e5d8b`
- Operator documentation: `a4daea7bc740aa7754847480794ab85c22faecca`

## Verification

- Static source review: completed.
- Local Python tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real MP4: NOT PROCESSED.
- Upload, publishing, merge, deployment: NOT PERFORMED.

## Guardrails

Continue on existing PR #386 and branch `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`. Preserve its original base and ancestry, OPEN / DRAFT / UNMERGED state. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real-media processing, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
