# ARO-CHAT-0236 | Strict Source URL Hostname Validation

- Chat ID: ARO-CHAT-0236
- Workstream ID: ARO-GTA-P1-236
- Priority: P1, fail-closed source-rights URL validation
- Parent: PR #371 / ARO-CHAT-0235
- Branch: `workstream/aro-chat-0236-strict-source-url-hostname-validation-2026-11-25`
- Base: PR #371 branch `workstream/aro-chat-0235-rights-registry-strict-text-timestamps-2026-11-25`
- Starting SHA: `2032ccbc1c115426e3731415915656841c2633ad`

## Finding

The existing URL guard checked scheme, authority, hostname presence, whitespace, port syntax/range, embedded credentials, and raw control/backslash characters. However, a non-empty hostname could still contain malformed DNS labels, such as empty interior labels, leading/trailing hyphens, underscores, or percent-encoded host text.

## Changes

- Add `_valid_hostname()` to validate IPv6 literals with Python's standard-library `ipaddress` parser.
- Validate DNS/IDNA hostnames by ASCII IDNA conversion, total/label length limits, and conservative DNS label character/boundary rules.
- Permit a single terminal dot for fully-qualified DNS names.
- Add invalid-host regressions for malformed labels, underscores, and percent-encoded host text.
- Add positive regressions for IPv6 literals, IDNA hostnames, and fully-qualified DNS names.
- No uploader, OAuth, media, workflow, or publishing behavior changed.

## Commits

- Production: `a58e30cd21f55cdabc0ff90103fc7a01e6b4e6b8`
- Tests: `4b6eabc429196e449e91e3119535a575eb2392f3`

## Validation

- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: PENDING until the draft PR's naturally triggered run is inspected.
- Independent security review: NOT RECORDED.
- Previous PR #371 run #45494763114 failed with zero exposed job steps and BlobNotFound logs; its failure cause remains NOT VERIFIED and is not attributed to source code.

## Safety

Draft only. No merge, rebase, retarget, workflow retry/dispatch, OAuth, credentials, real media, upload, deployment, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled.


### DNS hostname length boundary follow-up — 2026-11-25

- Added test-only regressions for a 64-character DNS label, a 254-character hostname, and a valid 253-character hostname composed of maximum-length labels.
- Also reject multiple terminal dots explicitly.
- Test commit: `83f970b608af3f49e6bf6c496d6de6918dc24bf7`.
- Local tests NOT RUN; exact-head Ubuntu/hosted-Windows CI PENDING / NOT VERIFIED. This commit does not change production behavior.
- PR #373 remains draft/open/unmerged. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
