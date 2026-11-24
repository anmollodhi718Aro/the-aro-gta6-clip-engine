# ARO-CHAT-0235 | Strict Rights Metadata and Timestamp Validation

- Chat ID: ARO-CHAT-0235
- Workstream ID: ARO-GTA-P1-235
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Branch: `workstream/aro-chat-0235-rights-registry-strict-text-timestamps-2026-11-25`
- Base: PR #369 head `8185687919138671deff872f6a7f35f86eafc27c`
- Scope: strict text-field and timestamp type validation at the source-rights registry boundary; no uploader, OAuth, media, or publishing changes.

## Finding

The preceding rights-registry input-validation branch still coerced source identity fields with `str(...)`. Non-string grant metadata could therefore be silently converted into persisted text. Its timestamp helper also called string methods on unvalidated values, allowing incidental exceptions rather than a deliberate fail-closed `ValueError`. Explicit falsey timestamp arguments could also be replaced by the current time through `at or now`.

## Changes

- Require `source_id`, `source_url`, `grantor`, and `evidence_ref` to be non-empty strings before normalization.
- Require supplied `attribution` and `disclosure` values to be strings; do not stringify nulls or arbitrary objects.
- Make timestamp parsing accept only timezone-aware `datetime` values or non-empty ISO timestamp strings.
- Validate an explicitly supplied `at` value even when falsey; only `None` selects the current time.
- Add regression tests for malformed required/optional text fields, malformed `valid_from`/`expires_at`, and invalid explicit timestamps to `authorize`/`revoke`.

## Commits

- Production: `42011adcb725a171d30ee496b37df47f00b01678`
- Tests: `5f305f66e2e47582fe651886ff3ca8b53843bcc9`

## Validation

- Local tests: NOT RUN in this connector session.
- PR #369 current head `8185687919138671deff872f6a7f35f86eafc27c`: associated Python CI run #45485759897 completed FAILURE. Job-step/log details were unavailable through the connector; failure cause is NOT VERIFIED.
- This branch's exact-head Ubuntu/hosted-Windows CI: PENDING until its own run is observed and inspected. No parent CI is transferred.
- Independent security review: NOT RECORDED.

## Safety

Draft-only. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled. No OAuth, credentials, real media, network upload, workflow retry/dispatch, merge, rebase, retarget, deployment, or publishing.
