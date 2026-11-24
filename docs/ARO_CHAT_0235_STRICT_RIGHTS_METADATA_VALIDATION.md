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


## Source URL validation follow-up

- Static review found that checking only an `http://` or `https://` prefix accepted malformed authorities such as `https://` and invalid ports.
- The registry now parses the URL authority, requires an HTTP(S) scheme and non-empty whitespace-free hostname, validates port syntax/range, and rejects embedded URL credentials.
- Regression tests cover empty/missing hosts, unsupported schemes, invalid/out-of-range ports, embedded credentials, whitespace in hostnames, and valid HTTP/HTTPS URLs.
- Production and test changes are committed on the existing ARO-CHAT-0235 branch. Local execution and fresh exact-head CI remain pending.


## URL parser ambiguity hardening

- Reject raw URL whitespace, including embedded CR/LF/tab, ASCII control characters, DEL, and backslashes before URL parsing.
- This avoids accepting values that parsers may normalize or interpret differently across layers.
- Added regression cases for newline, tab, and backslash-containing URLs.
- Production commit: 0380133cb38d5067b6d6016d41c42b72071babbd.
- Test commit: a94b6e6fae9d9789e11f74fa2233a347d0a46701.
- Local tests NOT RUN; final-head CI and independent review remain pending.


## URL validation regression-test correction — 2026-11-25

- Static inspection of the exact PR #371 head found a test assertion mismatch: whitespace/control/backslash inputs correctly raise the dedicated message `source_url must not contain...`, while the test incorrectly required the different `source_url must be a valid...` message.
- Test-only correction commit: `4a010129a1822e7a6658491981f28725e2be12fe`; the malformed URL cases now assert the required `ValueError` type without coupling to one of the valid fail-closed messages.
- Exact-head workflow lookup for this correction returned no associated run at inspection. Local tests NOT RUN; Ubuntu/hosted-Windows CI PENDING / NOT VERIFIED.
- The prior run `45486979384` failed on both jobs, but both exposed zero steps and no logs. That run does not establish the failure cause; the assertion mismatch is a separately confirmed static test defect.
- Draft PR #371 remains open and unmerged. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.


## Test-fixture correction — 2026-11-25

- Static review found two URL regression inputs encoded a literal backslash followed by `n`/`t`, rather than actual newline/tab characters.
- Test-only commit `77adf4b3541792b1151159bc5a2f02ec93a2369c` corrects those inputs so the tests exercise literal newline and tab rejection by the existing raw-URL guard.
- No production behavior changed. Local tests NOT RUN. Exact-head Ubuntu/hosted-Windows CI must be inspected on the final synchronized branch head. Earlier run #45486979384 failed with both jobs exposing zero steps and no logs; cause NOT VERIFIED.
- PR #371 remains draft/open/unmerged; independent review NOT RECORDED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
