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
- PR-head-associated Actions run #45462145169 completed SUCCESS on 2026-11-25. Both `tests` (Ubuntu) and `windows-tests` jobs completed compile, unit-test, and synthetic MP4/FFprobe steps successfully. The connector did not expose numeric test totals or the checked-out merge/head SHA, so raw-head-only execution and exact checkout identity are NOT VERIFIED.
- Independent security review: NOT RECORDED.
- Do not transfer parent PR #355 CI evidence to this branch. This run is associated with PR #357's then-current branch tip `5e8dc2baeb822a988fc527d1cba3f35fc4bc5e1f`; checkout identity is not independently exposed.
- Ancestry check against PR #355's recorded current head `4ceba80e02f28c52946d3d143cbb7fa4e31d611e` reports DIVERGED: 3 commits ahead / 10 behind; merge base `f2bd2982216280852f5b823796dc3700c16f2e7d`. Parent branch advanced after this branch's starting point. Preserve the draft; no rebase, retarget, or merge.

## Safety

- Test-only change. No production uploader, OAuth, token, rights decision, media, or workflow configuration changes.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
- No OAuth or credentials access, real media, network upload, publishing, workflow dispatch/retry, merge, rebase, retarget, deployment, or destructive action.
- Keep live uploads and public publishing disabled.
