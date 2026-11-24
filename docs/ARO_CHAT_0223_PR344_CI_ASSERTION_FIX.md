# ARO-CHAT-0223 — PR #344 CI assertion correction

Date: 2026-11-24

## Identity and scope
- Chat ID: ARO-CHAT-0223
- Workstream ID: ARO-GTA-P1-223
- Branch: `workstream/aro-chat-0223-pr344-ci-assertion-fix-2026-11-24`
- Base: PR #344 branch `workstream/aro-chat-0219-revalidate-rights-report-before-upload-2026-11-24`
- Starting SHA: `d2e057734517c1dfb3be994eb7268580f1f173a4`
- Scope: test-only correction for the exact-head CI failure on PR #344. No production uploader behavior changed.

## Evidence
- PR #346 workflow run #45441375437 failed on Ubuntu and hosted Windows.
- Ubuntu: 352 tests, 1 failure.
- Hosted Windows: 352 tests, 1 failure and 3 FIFO-only skips.
- Both failures were in `test_upload_rechecks_latest_rights_report_before_api_insert`.
- The implementation raised `PermissionError: no recorded rights for source source-2`, correctly rejecting a newly introduced source-bound asset with no rights record.
- The test expected the stale substring `no recorded rights for source-2`, omitting the word `source` before the source ID.
- The API insert was not reached; the test's fail-closed expectation remains intact.

## Change
- Updated only the test's expected error substring to match the actual, descriptive rejection message.
- Production code in `backend/app/youtube_upload.py` is unchanged.
- Commit: `9e349ae9fa6d66832b8d030e2ffe3bef55cdf35d`.

## Validation
- Exact-head CI for this follow-up: PENDING / NOT VERIFIED.
- Local tests: NOT RUN in this connector session.
- Do not transfer PR #346's failed run or any earlier run to this new head.
- The prior run checked out PR #346's merge ref `01092d8a49a041f45614a4c2fbd545dbb5057b40`, not the raw head alone.

## Safety and remaining gates
- Draft-only follow-up. No workflow retry/dispatch, OAuth, credentials, real media, network upload, publishing, merge, rebase, retarget, deployment, or destructive action.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; independent security review and owner-device OAuth/channel acceptance remain NOT RECORDED / NOT VERIFIED.
- Keep live uploads and public publishing disabled.
