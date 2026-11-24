# ARO-CHAT-0229 | Atomic Rights-Revocation Audit Rollback

- Chat ID: ARO-CHAT-0229
- Workstream ID: ARO-GTA-P1-229
- Exact chat title: ARO-CHAT-0229 | Verify Atomic Rights-Revocation Audit Rollback
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: workstream/aro-chat-0229-atomic-revocation-audit-rollback-2026-11-25
- Base: `workstream/aro-chat-0228-atomic-rights-revocation-2026-11-25` (PR #359 branch)
- Scope: test-only regression; production rights registry, uploader, OAuth, and workflow behavior unchanged.

## Finding and invariant
`SourceRightsRegistry.revoke()` updates the rights row and writes its audit event inside one SQLite transaction. A failure while inserting the audit event must roll back the preceding revocation update. Otherwise the source could be revoked without a corresponding audit record.

## Change
- Install a temporary SQLite trigger that rejects only `revoked` audit inserts.
- Assert the synthetic `sqlite3.IntegrityError` propagates.
- Assert the grant remains authorizable after the failed revoke.
- Assert the audit history still contains only the original registration event.

## Validation
- Test added to `tests/test_rights_registry.py`.
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu and hosted-Windows CI: PENDING until PR creation and run completion.
- Independent security review: NOT RECORDED.
- Owner-device Windows, authorized real-media, upload, and publishing acceptance: NOT VERIFIED.

## Safety
- Test uses temporary SQLite state only; no production behavior changed.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
- No OAuth, credentials, real media, network upload, publishing, workflow dispatch/retry, merge, rebase, retarget, deployment, or destructive action.
- Keep live uploads and public publishing disabled.
