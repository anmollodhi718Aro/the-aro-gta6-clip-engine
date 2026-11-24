# ARO-CHAT-0232 | Validate public source-rights registry inputs

Date: 2026-11-25

## Workstream
- Chat ID: ARO-CHAT-0232
- Exact title: ARO-CHAT-0232 | Validate Public Rights Registry Inputs
- Workstream: ARO-GTA-P1-232
- Branch: `workstream/aro-chat-0232-rights-registry-public-input-validation-2026-11-25`
- Base / starting SHA: PR #362 current branch head `a39fd8ed3db36e8aae98cfc902c10f7fe36e7054`
- Parent: PR #362, stacked on the rights-registry validation/concurrency workstream.

## Finding
The persistent source-rights registry's public methods used string operations before validating argument types. Non-string or container values passed to `authorize()`, `revoke()`, or `audit_events()` could raise incidental `AttributeError`/SQLite binding errors rather than a predictable validation error. `register()` also assumed its record argument was a dictionary and coerced identity fields to strings.

## Changes
- Add shared required-text and timestamp validators that reject malformed values with `ValueError`.
- Validate and normalize source ID, use, platform, actor, grantor, evidence reference, and source URL before persistence or lookup.
- Reject non-mapping registration records and non-text identity fields instead of silently coercing them.
- Add regressions covering malformed text and timestamp values across `register()`, `authorize()`, `revoke()`, and `audit_events()`.
- No changes to grant scope semantics, immutable grant behavior, SQLite transaction boundaries, uploader, OAuth, media ingestion, or publishing.

## Validation
- Implementation commits: `94067f2974f7c6ebcea6415ccfae72b66d521255`, timestamp validation `33c36a359e3438fbc9e76fc6b1cf7d0ffba979ef`; tests: `ec18f4f45ec8e1a5c0ff8be64e8c2cff1f83ec49`, timestamp regressions `cf2cfecbe910e94929f17cbde16da4e00d3268e2`.
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu / hosted-Windows CI: PENDING.
- Independent security review: NOT RECORDED.
- Owner-device Windows and authorized real-media acceptance: NOT VERIFIED.

## Safety
Draft only. No OAuth, credentials/tokens, real media, upload, publishing, workflow retry/dispatch, merge, rebase, retarget, deployment, or destructive action. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
