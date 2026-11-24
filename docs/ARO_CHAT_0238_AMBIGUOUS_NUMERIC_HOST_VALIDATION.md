# ARO-CHAT-0238 | Reject Ambiguous Numeric URL Hosts

- Chat ID: ARO-CHAT-0238
- Workstream ID: ARO-GTA-P1-238
- Priority: P1, fail-closed source-rights URL validation
- Parent: PR #373 hostname validation and PR #374 static audit
- Branch: `workstream/aro-chat-0238-ambiguous-numeric-hostname-rejection-2026-11-25`
- Base: PR #374 head `bd458946572ca5cec66f4ea55064d8596bf4ad3c`

## Finding

The DNS label validator accepted numeric-only host strings such as `127.1` and `2130706433`. Although these pass generic DNS-label character checks, URL consumers and system resolvers may interpret them as shorthand IPv4 addresses. That parser differential makes the accepted destination ambiguous.

## Change

- Keep IPv6 validation unchanged.
- Treat hosts made only of decimal digits and dots as IPv4 candidates.
- Accept those candidates only when Python's standard-library `IPv4Address` parser recognizes canonical four-octet IPv4 notation.
- Reject malformed dotted quads and shortened/integer IPv4 forms.
- Add negative regression cases for `999.999.999.999`, `127.1`, and `2130706433`.
- Add a positive canonical IPv4 regression case (`192.0.2.1`).
- No DNS resolution, destination-IP filtering, uploader, OAuth, media, workflow, or publishing behavior is changed.

## Validation

- Local tests NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI PENDING.
- Independent security review NOT RECORDED.

## Safety

Draft-only. No workflow retry/dispatch, merge, rebase, retarget, deployment, credentials, OAuth, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
