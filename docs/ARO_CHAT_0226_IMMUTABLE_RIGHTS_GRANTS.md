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


## Metadata immutability regression follow-up
- Expanded the active duplicate-ID test to attempt replacing the source URL, grantor, evidence reference, attribution, disclosure, allowed uses, and platforms.
- The test now asserts that the original stored grant metadata remains unchanged after the duplicate attempt.
- Test-only commit: `33743ca5ecaab1d69cab999968e8da8dc7f030ae`.
- Local tests NOT RUN in this connector session. The prior CI run applies to the earlier head only; verify the new exact head separately.


## Platform/use-scope regression follow-up — 2026-11-25

- Added explicit assertions that a duplicate source-ID registration cannot add the `tiktok` platform or broaden the original `analyze`-only grant to `edit`.
- Test-only commit: `5befa5058e3d018dca999a98b6ab564edc8c3f30`; production code unchanged.
- The updated PR #355 head is `5befa5058e3d018dca999a98b6ab564edc8c3f30`.
- Commit-associated workflow lookup returned no runs. Exact-head Ubuntu/hosted-Windows CI remains PENDING / NOT VERIFIED; local tests were NOT RUN in this connector session.
- PR #355 remains OPEN / DRAFT / UNMERGED. Its base PR #354 advanced independently; comparison reports DIVERGED (10 commits ahead / 2 behind; merge base `1d9d478fcfd03e36f6389acca682b3ede57c17fd`). No rebase, retarget, or merge was performed.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled. No OAuth, credentials, real media, upload, workflow dispatch/retry, deployment, or publishing occurred.

## SQLite error-classification hardening — 2026-11-25

- Static review found the duplicate-source handler translated every `sqlite3.IntegrityError` into a duplicate-grant `PermissionError`, potentially hiding unrelated database integrity failures.
- Production follow-up now translates only SQLite primary-key/unique constraint codes; all other integrity errors are re-raised unchanged.
- Production commit: `b8f17e4f7278d4996b931a980a54207b14170f29`.
- Added a trigger-based regression proving a non-duplicate SQLite integrity failure remains an `sqlite3.IntegrityError` and writes no audit event.
- Test commit: `b459ad87a0908fd3dc98479b663f7c2695ed12a7`.
- Local tests NOT RUN. Exact-head Ubuntu/hosted-Windows CI lookup for test commit returned zero runs; CI PENDING / NOT VERIFIED. Independent security review NOT RECORDED.
- PR #355 remains draft/open/unmerged. Branch ancestry against current PR #354 head `cac64637a9cdc64eded472ab4d9c6ed0323d4b19` is DIVERGED (15 ahead / 7 behind; merge base `1d9d478fcfd03e36f6389acca682b3ede57c17fd`). No rebase, retarget, or merge.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled. No OAuth, credentials, real media, upload, workflow retry/dispatch, deployment, or publishing.
