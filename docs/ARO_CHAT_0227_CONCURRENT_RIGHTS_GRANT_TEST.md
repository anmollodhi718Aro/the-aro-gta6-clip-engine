# ARO-CHAT-0227 | Concurrent Immutable Rights Registration Regression

- Chat ID: ARO-CHAT-0227
- Workstream ID: ARO-GTA-P1-227
- Parent: PR #355, head `f2bd2982216280852f5b823796dc3700c16f2e7d`
- Branch: `workstream/aro-chat-0227-atomic-rights-grant-concurrency-2026-11-25`
- Scope: test-only regression coverage; no production code or uploader behavior changed.

## Rationale

PR #355 changes source-rights registration to a single INSERT and rejects duplicate primary keys. This follow-up adds a two-worker concurrent registration regression to exercise the uniqueness boundary under competing calls, rather than only sequential duplicate attempts.

## Change

- Synchronize two worker threads so both attempt to register the same source ID concurrently.
- Assert exactly one call registers and the other fails closed with PermissionError.
- Assert exactly one `registered` audit event exists and its actor is one of the two workers.
- Existing sequential duplicate, metadata-preservation, platform/use-scope, and revoked-grant tests remain intact.

## Validation

- GitHub branch/file writes completed.
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu and hosted-Windows CI: PENDING until PR workflow reports.
- Independent security review: NOT RECORDED.
- No test result is inferred from parent PR #355 or its earlier CI.

## Safety

- Test-only change. No production uploader, OAuth, token, rights decision, media, or workflow configuration changes.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
- No OAuth or credentials access, real media, network upload, publishing, workflow dispatch/retry, merge, rebase, retarget, deployment, or destructive action.
- Keep live uploads and public publishing disabled.
