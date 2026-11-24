# ARO-CHAT-0228 | Rights registry validation and concurrency reconciliation

Date: 2026-11-25

## Workstream
- Chat ID: ARO-CHAT-0228
- Workstream ID: ARO-GTA-P1-228
- Scope: consolidate the useful input-validation and concurrent-duplicate-registration regressions onto the latest immutable-rights parent head, without rewriting or closing earlier draft branches.
- Branch: `workstream/aro-chat-0228-rights-registry-validation-concurrency-2026-11-25`
- Base: PR #355 branch `workstream/aro-chat-0226-rights-grant-no-overwrite-2026-11-24`
- Starting SHA: `4ceba80e02f28c52946d3d143cbb7fa4e31d611e`

## Why this continuation exists
- PR #356 contains useful scope/platform collection validation, but its branch is based on the older `ac95ccc7e3eda5ab83621bb4652c24cecf873d8e` ancestor and its copy of `rights_registry.py` still translates every `sqlite3.IntegrityError` into a duplicate-grant `PermissionError`. That loses the narrower SQLite primary-key/unique error classification now present in PR #355.
- PR #357 adds useful concurrent duplicate-registration coverage, but its branch is also diverged from PR #355's current head.
- A fresh branch was created from PR #355's latest observed head. The earlier PRs remain untouched; no rebase, retarget, merge, or close was performed.

## Changes
- Port collection validation for `allowed_uses` and `platforms`: accept only list/tuple/set/frozenset collections of non-empty strings; reject scalar strings, empty collections and malformed members.
- Validate `actor` as a non-empty string and raise the documented `ValueError` for invalid values.
- Preserve the parent branch's narrower SQLite integrity-error classification.
- Add concurrent duplicate-registration coverage: two synchronized workers race for one source ID; exactly one registration succeeds, one fails closed, and exactly one registration audit event is recorded.
- No OAuth, uploader, publishing, media-ingestion, or workflow behavior changed.

## Commits
- Production validation: `318970c09c53e239bdbf89a52e6f154cba1b3745`
- Regression tests: `15f2d7cd0820e68409898cffe095a872ff4a6f37`

## Validation status
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: PENDING / NOT VERIFIED for the final branch head.
- Independent security review: NOT RECORDED.
- Owner-device Windows and authorized real-media acceptance: NOT VERIFIED.
- CI results from PR #355, #356, or #357 are not transferred to this branch.

## Safety
- Draft-only continuation. Keep public uploads and live publishing disabled.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
- No OAuth, credentials/tokens, real media, network upload, publishing, workflow retry/dispatch, merge, rebase, retarget, deployment, or destructive action.
