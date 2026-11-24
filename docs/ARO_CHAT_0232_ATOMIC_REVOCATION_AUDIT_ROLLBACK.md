# ARO-CHAT-0232 | Atomic revocation audit rollback regression

Date: 2026-11-25

## Workstream
- Chat ID: ARO-CHAT-0232
- Exact chat title: ARO-CHAT-0232 | Port Atomic Revocation Rollback Regression
- Workstream ID: ARO-GTA-P1-232
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: workstream/aro-chat-0232-atomic-revocation-audit-rollback-port-2026-11-25
- Base / starting SHA: PR #362 latest observed head `a39fd8ed3db36e8aae98cfc902c10f7fe36e7054`
- Related drafts: PR #360 (original regression on older branch); PR #362 (current rights-registry test line); PR #363 (separate documentation-only handoff branch, preserved unchanged)

## Scope and rationale
Port the existing atomic-revocation regression from PR #360 onto the newer PR #362 rights-registry line. The newer line contains the Windows-safe `contextlib.closing` fixture correction and current rights-registry validation/concurrency tests, but did not include this rollback invariant test.

## Change
- Add `test_revocation_and_audit_are_atomic_when_audit_insert_fails` to `tests/test_rights_registry.py`.
- Install a temporary trigger that rejects only the `revoked` audit insert.
- Assert the original `sqlite3.IntegrityError` propagates.
- Assert the grant remains authorizable and audit history contains only the original `registered` event, proving the rights update rolled back with the failed audit insert.
- Use `contextlib.closing` for the trigger fixture so Windows temporary-directory teardown does not retain an open SQLite handle.
- No production code, uploader, OAuth, media, workflow, or publishing behavior changed.

## Commits and validation
- Test commit: `98f20b1a657169b4bd3f6d85d4de7dd4197c655d`.
- Local tests in this connector session: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: pending PR creation / automatic run; NOT VERIFIED until both jobs pass.
- Independent security review: NOT RECORDED.
- This is synthetic SQLite state only. No credentials, OAuth, real media, upload, or publishing.

## Safety and disposition
- Draft-only continuation; preserve PRs #360, #362, and #363 unchanged. No rebase, retarget, merge, workflow retry/dispatch, deployment, or destructive action.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled.
