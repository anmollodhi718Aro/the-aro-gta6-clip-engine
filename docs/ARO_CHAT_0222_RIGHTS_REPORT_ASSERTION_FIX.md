# ARO-CHAT-0222 — Rights-report rejection assertion correction

Date: 2026-11-24

## Identity and scope
- Chat ID: ARO-CHAT-0222
- Workstream ID: ARO-GTA-P1-222
- Parent: PR #344, rights-report revalidation before upload
- Branch: `workstream/aro-chat-0222-rights-report-test-message-fix-2026-11-24`
- Base / starting SHA: `d2e057734517c1dfb3be994eb7268580f1f173a4`
- Scope: test-only correction for an assertion mismatch exposed by PR #346 CI.

## Evidence
- PR #346 workflow run #45441375437 completed with Ubuntu and hosted-Windows test jobs failing.
- Both platforms ran 352 tests; the same single test failed on each.
- `test_upload_rechecks_latest_rights_report_before_api_insert` correctly received the fail-closed error `no recorded rights for source source-2`, but its regex expected `no recorded rights for source-2`.
- The failure is an assertion-text mismatch. The rights rejection occurred and the mocked YouTube insert was not reached.

## Change
- Updated only the expected error text in `tests/test_youtube_upload.py`.
- Production uploader, approval logic, rights checks, and workflow configuration are unchanged.
- Commit: `43434965bd0b0607f3e95077d5abb4f4710ae1a3`.

## Validation
- Local tests: NOT RUN in this connector session.
- New branch exact-head Ubuntu / hosted-Windows CI: PENDING.
- Do not transfer PR #346's failed run to the new branch as validation.
- No OAuth, credentials/tokens, real media, network upload, publishing, merge, rebase, retarget, deployment, or destructive action.

## Safety and status
- Test correction: IMPLEMENTED.
- CI: PENDING / NOT VERIFIED.
- PR remains draft until opened; no merge authorized.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
