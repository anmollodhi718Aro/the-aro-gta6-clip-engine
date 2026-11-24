# ARO-CHAT-0228 | Concurrent Source-Rights Revocation Regression

- Chat ID: ARO-CHAT-0228
- Workstream ID: ARO-GTA-P1-228
- Exact chat title: Continue coding
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0228-atomic-rights-revocation-2026-11-25`
- Base / starting SHA: `4ceba80e02f28c52946d3d143cbb7fa4e31d611e` (PR #355 current recorded head)
- Scope: test-only regression; production rights registry, uploader, OAuth and workflow behavior unchanged.

## Change
- Synchronize two workers attempting to revoke the same registered source ID.
- Assert exactly one call returns `True` and the competing call returns `False`.
- Assert the audit history contains one registration and exactly one revocation, attributed to one of the two workers.
- Uses temporary SQLite state and local threads only.

## Validation
- Source test update committed on the isolated branch.
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu and hosted-Windows CI: PENDING until a PR exists and its own head run completes.
- Independent security review: NOT RECORDED.
- This test does not establish owner-device Windows, real-media, upload, or publishing acceptance.

## Safety
- No production code or uploader behavior changed.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
- No OAuth, credentials, real media, network upload, publishing, workflow dispatch/retry, merge, rebase, retarget, deployment, or destructive action.
- Keep live uploads and public publishing disabled.
