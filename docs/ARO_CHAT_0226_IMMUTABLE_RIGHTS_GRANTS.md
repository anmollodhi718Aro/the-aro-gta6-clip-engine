# ARO-CHAT-0226: Immutable source-rights grant identity

Date: 2026-11-24

## Scope
Carry the duplicate-grant protection into the active rights-report hardening lineage. The inspected PR #354 branch still contained an UPSERT in `SourceRightsRegistry.register()`, despite a separate draft PR #352 having explored the same fix on another branch.

## Finding
The prior UPSERT updated an existing `source_id` and set `revoked_at=NULL`. Re-registering the same source ID could replace grant evidence, broaden permitted uses/platforms, or reactivate a revoked grant. A separate branch's implementation is not inherited unless its commits are in this branch's ancestry.

## Change
- Use INSERT-only registration for source IDs.
- Convert duplicate-key integrity failures into an explicit `PermissionError`.
- Do not write a second audit event for a rejected duplicate.
- Require a new source ID for a new grant; no reinstatement workflow is introduced.

## Regression coverage
- An analyze-only grant cannot be broadened to publish by re-registering the same source ID.
- A revoked source ID cannot be re-registered to clear its revocation.
- The original permission and audit history remain intact after duplicate attempts.

## Branch ancestry
- Branch: `workstream/aro-chat-0226-rights-grant-no-overwrite-2026-11-24`
- Base: PR #354 branch `workstream/aro-chat-0225-stable-rights-report-read-2026-11-24`
- Base PR: #354, itself stacked on PR #353.
- Production commit: `a9716c4e5d39b79103dfed2ee000cd817db71b0b`
- Test commit: `8cc3155cf39c75b5a9e28b1f9a17a44a13264530`

## Validation and status
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu and hosted-Windows CI: PENDING until PR checks are observed.
- Independent security review: NOT RECORDED.
- Owner-device acceptance: NOT VERIFIED.
- This is a draft implementation, not a claim that the whole uploader pipeline is secure.

## Safety
No OAuth login, credentials/tokens, real media, network upload, publishing, workflow retry/dispatch, merge, rebase, retarget, deployment, or destructive action was performed. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
