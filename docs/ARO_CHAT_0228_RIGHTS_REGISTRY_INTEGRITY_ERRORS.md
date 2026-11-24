# ARO-CHAT-0228: Preserve unrelated rights-registry integrity errors

## Identity
- Chat title: ARO-CHAT-0228 | Preserve Rights-Registry Integrity Errors
- Workstream: ARO-GTA-P1-228
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0228-rights-registry-integrity-errors-2026-11-25`
- Base: PR #356 branch `workstream/aro-chat-0227-rights-registry-input-validation-2026-11-25`
- Starting point: PR #356 implementation branch tip, resolved by GitHub when the branch was created

## Finding
PR #356 adds strict collection and actor validation, but its INSERT handler translates every `sqlite3.IntegrityError` into `PermissionError`. Only a primary-key/unique-key collision represents an existing immutable source grant. A trigger, CHECK, NOT NULL, or other unrelated integrity failure must remain diagnosable as its original database error.

## Change
- Translate only `SQLITE_CONSTRAINT_PRIMARYKEY` and `SQLITE_CONSTRAINT_UNIQUE` into the existing duplicate-grant `PermissionError`.
- Re-raise all other SQLite integrity errors unchanged.
- Add a trigger-based regression that produces `SQLITE_CONSTRAINT_TRIGGER`, asserts the original `sqlite3.IntegrityError` propagates, and verifies no registration audit event is written.
- Preserve PR #356's input validation and INSERT-only grant behavior.

## Validation
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: PENDING until GitHub Actions reports results for this branch's final head.
- Independent security review: NOT RECORDED.
- Owner-device Windows and authorized real-media acceptance: NOT VERIFIED.

## Safety
Draft-only code/test hardening. No OAuth, credentials, real media, network upload, publishing, workflow retry/dispatch, merge, rebase, retarget, deployment, or destructive action. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
