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


## Windows CI cleanup correction — 2026-11-25

- Exact-head workflow run #45464223565 ran against PR #359 merge ref `f7c489e5d2675b9c9a06ef019d23426c84c09da2`, containing PR head `24ddb8fc84fa6e61cbcbfb1b2c38848587d269ee` merged into base `4ceba80e02f28c52946d3d143cbb7fa4e31d611e`.
- Ubuntu job #138694681391 passed compilation, unit tests, and synthetic MP4/FFprobe.
- Hosted-Windows job #138694681825 compiled successfully but failed during unit-test cleanup: `test_non_duplicate_integrity_error_is_not_misreported_as_duplicate` left the SQLite connection open because the SQLite connection context manager commits/rolls back but does not close the connection. Windows then raised `PermissionError [WinError 32]` while TemporaryDirectory cleanup tried to remove `rights.sqlite3`. Synthetic MP4/FFprobe was skipped after the test failure.
- Test-only correction commit `bf1e57e180bc08b78bdc0e5c1243850db12ce8df` imports `contextlib.closing` and explicitly closes the SQLite connection used to create the synthetic trigger.
- Production code and revocation behavior are unchanged. Fresh exact-head Ubuntu/hosted-Windows CI is required; local tests NOT RUN in this connector session. Do not transfer run #45464223565 as a pass for the corrected head.
- PR #359 remains draft/open/unmerged. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. No workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, merge, rebase, retarget, deployment, or destructive action. Keep live uploads/public publishing disabled.
