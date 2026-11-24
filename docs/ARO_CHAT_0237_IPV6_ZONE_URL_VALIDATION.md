# ARO-CHAT-0237 | Strict IPv6 URI Zone Identifier Validation

- Chat ID: ARO-CHAT-0237
- Exact chat title: ARO-CHAT-0237 | Strict IPv6 URI Zone Identifier Validation
- Workstream ID: ARO-GTA-P1-237
- Parent: PR #373 / ARO-CHAT-0236
- Branch: `workstream/aro-chat-0237-ipv6-zone-url-validation-2026-11-25`
- Base: PR #373 head `ce0f784dcaace436214ae94c04e9a81b8f767a5d`

## Finding

The hostname validator delegated any IPv6-like value to `ipaddress.IPv6Address`. Python accepts scoped IPv6 strings such as `fe80::1%eth0`, including when supplied as the URI host by `urlsplit`. A URI zone delimiter must be encoded as `%25`; accepting the raw `%eth0` form permits malformed URL authority syntax through the rights-registry boundary.

## Change

- Require the URI-encoded `%25` delimiter when a scoped IPv6 literal is present.
- Require a non-empty ZoneID containing only unreserved characters or well-formed percent-encoded octets.
- Validate the address portion independently with `ipaddress.IPv6Address`.
- Add negative regressions for an unescaped zone delimiter, an empty ZoneID, and a malformed percent escape.
- Add a positive regression for a correctly encoded scoped IPv6 URL.
- Preserve unscoped IPv6, DNS, IDNA and fully-qualified DNS handling.

## Commits

- Production: `85ba117d3e8a4dbe9f68a52996358719c7cee940`
- Tests: `9b0f0bd053dc63621f90e6359b8f22108b1428b4`

## Validation

- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: PENDING; do not transfer PR #373 or PR #371 CI.
- Independent review: NOT RECORDED.
- No real media, OAuth, credentials, upload, publishing, workflow retry/dispatch, merge, rebase, retarget or deployment.

## Safety

Draft-only validation hardening. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
