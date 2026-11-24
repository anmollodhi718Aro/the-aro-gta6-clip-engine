# ARO-CHAT-0219: Revalidate the current rights report before upload

**Date:** 2026-11-24  
**Workstream:** ARO-GTA-P1-219  
**Parent:** PR #339  
**Branch:** `workstream/aro-chat-0219-revalidate-rights-report-before-upload-2026-11-24`  
**Base / starting SHA:** `b0a5e3e1adcff9f7a2f3715b6ba7a0c138a50722`

## Finding

The consolidated uploader loaded the rights-preflight JSON once, checked its source-bound assets, then reused that in-memory object for the final pre-upload permission check. The source-rights registry was queried again, but a rights-report file changed after the initial read could add a source-bound asset without that newly added source being checked before the API insert.

## Change

- Keep the initial rights-report validation and permission check.
- Re-read and re-validate the rights-report file immediately before the YouTube insert.
- Re-check that the latest report still binds the exact requested clip ID and source ID.
- Re-run source and source-bound asset publish-permission checks against the latest report and current rights registry.
- Fail closed before the API insert if the report changed or any newly declared source lacks a current YouTube publish grant.

## Regression coverage

Added `test_upload_rechecks_latest_rights_report_before_api_insert`. The mocked test changes the report between the initial and final reads by adding a source-bound asset with an unregistered source ID. It asserts that the uploader rejects the missing grant and never calls the YouTube insert API.

## Commits

- Production: `56685d4edf88af8d15b2390283752792984427a5`
- Initial test: `70b86a1ead7f3f4c6c466dc79684041aac08ea18`
- Assertion correction: `0e3d54632d142d64d609aef6641ba6d295615941`

## Validation

- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu / hosted-Windows CI: PENDING.
- Independent security review: NOT RECORDED.
- Owner-device Windows and real-media acceptance: NOT VERIFIED.
- No OAuth credentials, real media, network upload, workflow retry/dispatch, merge, rebase, retarget, deployment, or publishing performed.

## Safety and next step

Draft-only follow-up stacked on PR #339. Issue #68 remains OPEN. Keep live uploads and public publishing disabled. Inspect this PR's own exact-head Ubuntu and hosted-Windows CI and review the full uploader/approval lineage; do not transfer predecessor CI evidence.


### PR #344 current-head and ancestry audit — 2026-11-24
- Draft PR #344 created against PR #339's branch; PR #344 head at audit: `f9688ebce4c1b8da646f1cf8289a92b1936a03c8`.
- PR #344 head-associated workflow lookup returned zero runs; exact-head Ubuntu/hosted-Windows CI is PENDING / NOT VERIFIED.
- The base branch advanced from starting SHA `b0a5e3e1adcff9f7a2f3715b6ba7a0c138a50722` to `6204a3979b8753919e3f983ce42a3777b3215d87` by 12 documentation-only commits. Compare reports PR #344 head 6 commits ahead and 12 behind the current base, with merge base at the starting SHA; status DIVERGED.
- Preserve PR #344 as DRAFT / OPEN / UNMERGED. No automatic rebase or retarget. Reconcile the documentation-only parent advancement with owner approval before ancestry changes.
- Local tests NOT RUN. Independent security review NOT RECORDED. Issue #68 remains OPEN. Keep live uploads/public publishing disabled.
