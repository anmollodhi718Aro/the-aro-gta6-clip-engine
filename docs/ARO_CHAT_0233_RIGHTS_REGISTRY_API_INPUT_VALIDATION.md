# ARO-CHAT-0233 | Rights registry API input validation

Date: 2026-11-25

## Workstream
- Chat ID: ARO-CHAT-0233
- Workstream ID: ARO-GTA-P1-233
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0233-rights-registry-api-input-validation-2026-11-25`
- Base / starting SHA: `332be0ef6063392388a98608c179a046f4d381be` (PR #363 documentation handoff head)
- Scope: fail early with stable ValueError responses when public rights-registry APIs receive malformed container or identifier types.

## Finding and change
- `register()` dereferenced `record.get` before checking that the record was a mapping.
- `authorize()` performed set membership and string methods before validating argument types, so malformed inputs could leak TypeError/AttributeError instead of the documented validation failure.
- `revoke()` similarly called `.strip()` on unvalidated source/actor values.
- Added explicit input checks before those operations and focused regression tests. Rights decisions, SQL statements, grant scopes, audit semantics, uploader behavior and publishing behavior are unchanged.

## Validation
- Implementation and regression tests are committed on this draft branch.
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: PENDING until GitHub Actions reports a run for the final PR head.
- Independent review: NOT RECORDED.

## Safety
Draft only. No OAuth, credentials/tokens, real media, network upload, workflow retry/dispatch, merge, rebase, retarget, deployment or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled.
