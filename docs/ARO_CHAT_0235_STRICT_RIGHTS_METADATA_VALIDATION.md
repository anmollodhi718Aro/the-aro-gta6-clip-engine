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


## Exact-head CI audit — 2026-11-25

- Audited PR #371 current head `bfa64a2953a6b046ff4cf2a23d8d9ba81b1a7346` on branch `workstream/aro-chat-0235-rights-registry-strict-text-timestamps-2026-11-25`.
- Commit-associated Python CI run [#45491714696](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45491714696) completed FAILURE.
- Ubuntu job `138791506600` and hosted-Windows job `138791505874` both report completed FAILURE. The connector exposed zero steps for both jobs; log retrieval for both returned `BlobNotFound`.
- Combined commit status returned zero status entries. PR #371 review submissions and inline review threads were empty at inspection. Independent review NOT RECORDED.
- The available evidence does not establish whether failure occurred during runner/workflow initialization or before the first step. Root cause NOT VERIFIED; do not attribute the failure to application code or tests.
- Local tests NOT RUN in this connector session. Exact-head CI status: FAILED / NOT VERIFIED. No test count or compile result is claimed.
- No workflow retry/dispatch was initiated. PR #371 remains DRAFT / OPEN / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
- No source, test, uploader, OAuth, media, or workflow behavior was changed in this audit. No credentials, real media, upload, publishing, merge, rebase, retarget, deployment, or destructive action was performed.


## Empty-port URL hardening — 2026-11-25

- Static review found `urllib.parse.urlsplit(...).port` returns `None` for an explicitly empty port (for example `https://example.com:/video`) rather than raising `ValueError`.
- The source-rights registry now rejects an authority whose netloc ends in `:` after parsing, covering both DNS and bracketed IPv6 authorities.
- Regression tests added for `https://example.com:/video` and `https://[::1]:/video`.
- Production commit: `15f68da1e3416ee2b785b5d4a47c140a11e43917`; test commit: `41d42e89eeb3adc9e7dd2607e4f7b638214d8982`.
- Local tests NOT RUN. Exact-head Ubuntu/hosted-Windows CI NOT YET OBSERVED; independent security review NOT RECORDED. PR #371 remains DRAFT / OPEN / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.


### Blank-text and falsey-timestamp regression follow-up — 2026-11-25

- Test-only follow-up on the existing ARO-CHAT-0235 branch; no new branch or PR.
- Added regression cases proving whitespace-only required rights text is rejected for source ID, source URL, grantor, and evidence reference.
- Added explicit falsey timestamp cases (empty string, False, and 0) for registration valid_from/expires_at and authorize/revoke at parameters. Only None remains the sentinel for selecting the current time in the latter methods.
- Test commit: 079d9213ab53142c6d085dbfc28597df745a5a2b; current PR #371 head at handoff: same SHA.
- Local tests NOT RUN in this connector session. Commit-associated workflow lookup returned no run at inspection; exact-head Ubuntu/hosted-Windows CI PENDING / NOT VERIFIED. Independent security review NOT RECORDED.
- PR #371 remains DRAFT / OPEN / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled. No OAuth, credentials, real media, upload, workflow retry/dispatch, merge, rebase, retarget, deployment, or publishing.

## Current exact-head CI recheck — 2026-11-25

- Re-fetched PR #371 metadata: OPEN / DRAFT / UNMERGED; exact head `2032ccbc1c115426e3731415915656841c2633ad`; base `8185687919138671deff872f6a7f35f86eafc27c`.
- Commit-associated workflow lookup returned Python CI run [#45494763114](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45494763114), run 1524, completed FAILURE.
- Ubuntu job `138802196403` and hosted-Windows job `138802196129` both completed FAILURE. The jobs endpoint exposed `steps: null`; the dedicated step lookup returned empty arrays for both jobs.
- Both job-log requests returned `BlobNotFound`. The available evidence does not identify a failing command, runner initialization cause, or application/test defect. Root cause NOT VERIFIED.
- Combined commit status returned zero status entries. PR #371 review submissions and inline review threads were empty at inspection; independent review NOT RECORDED.
- Local tests NOT RUN in this connector session. No compile result or test count is claimed. Exact-head CI: FAILED / NOT VERIFIED.
- No workflow retry/dispatch was initiated. Keep PR #371 DRAFT / OPEN / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
- No code, workflow, OAuth, credential, media, upload, publishing, merge, rebase, retarget, deployment, or destructive action was performed in this audit.
