# ARO-CHAT-0224 — Prevent source-rights overwrite and revocation reset

Date: 2026-11-24

## Identity and scope
- Chat ID: ARO-CHAT-0224
- Workstream ID: ARO-GTA-P1-224
- Branch: `workstream/aro-chat-0224-rights-registry-immutability-2026-11-24`
- Base: PR #350 branch `workstream/aro-chat-0223-pr344-ci-assertion-fix-2026-11-24`
- Starting SHA: `b6d712a6438a132c3d8ca245b0a804bf8b929550`
- Scope: make source-rights registrations immutable by source ID; prevent a later register call from overwriting an existing grant or clearing its revocation timestamp.

## Finding
The current `SourceRightsRegistry.register()` used SQLite `ON CONFLICT(source_id) DO UPDATE` and explicitly set `revoked_at=NULL`. Re-registering an existing source ID could therefore replace its grant evidence/scope and reactivate a revoked source without a distinct approval path.

## Change
- Replace the upsert with a plain INSERT.
- Convert duplicate source-ID integrity conflicts into a fail-closed `PermissionError`.
- Preserve the original row and audit trail on duplicate registration.
- Require a new source ID for a new grant; this change does not add a grant-reinstatement workflow.

## Regression coverage
- Duplicate registration cannot broaden or replace an existing active grant; the original narrower grant remains authoritative.
- Re-registering a revoked source ID is rejected; authorization remains revoked and audit events remain exactly `registered`, `revoked`.

## Commits
- Production: `87294298cd6f486d906f8964d4c9d590cf09dd9e`
- Tests: `5a9ef569c64b77151e60063f2b86cf967e60edd2`

## Validation
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu and hosted-Windows CI: PENDING / NOT VERIFIED.
- PR #350 exact-head CI run #45442036637 passed on Ubuntu and hosted Windows, but it validates the parent SHA `b6d712a6438a132c3d8ca245b0a804bf8b929550`, not this branch's new commits. No result is transferred.
- No OAuth credentials, real media, network upload, publishing, workflow retry/dispatch, merge, rebase, retarget, deployment, or destructive action.

## Safety and remaining gates
- Draft-only; keep PRs unmerged pending independent security review and owner-controlled acceptance.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
- Keep live uploads and public publishing disabled.
