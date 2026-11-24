# ARO-CHAT-0237 | Canonical IPv4 URL Host Validation

- Chat ID: ARO-CHAT-0237
- Workstream ID: ARO-GTA-P1-237
- Priority: P1, fail-closed source-rights URL validation
- Parent: PR #373 / ARO-CHAT-0236
- Branch: `workstream/aro-chat-0237-canonical-ipv4-host-validation-2026-11-25`
- Base: PR #373 branch `workstream/aro-chat-0236-strict-source-url-hostname-validation-2026-11-25`
- Starting SHA: `ecd35c1c4170f038b57ece0d5df976b80de5c276`

## Finding

The preceding hostname validator accepted every host whose labels matched DNS syntax. That also admitted ambiguous numeric forms such as shorthand IPv4 (`127.1`), octal (`0177.0.0.1`), hexadecimal (`0x7f.0.0.1`), invalid dotted-decimal addresses, and numeric-ending names such as `example.123`. URL consumers can interpret some of these forms differently from a strict DNS hostname validator.

## Changes

- Detect URL-parser numeric final labels (decimal, octal-style, and hexadecimal-style).
- If the final label has a numeric URL-host form, accept the host only when Python's standard-library `ipaddress.IPv4Address` accepts the entire host as canonical dotted-decimal IPv4.
- Preserve DNS/IDNA, IPv6, and single-trailing-dot FQDN behavior for non-ambiguous names.
- Add regression coverage for invalid dotted decimal, shorthand, octal, hexadecimal, numeric-ending DNS labels, and a valid canonical IPv4 address.
- No uploader, OAuth, media, workflow, or publishing behavior changes.

## Commits

- Production: `bcaed58a8f118b685aec0049e99827726e1da690`
- Tests: `54de8745d1bd6ef5ef137b4894cbb3fcf16f2520`

## Validation

- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: PENDING until a naturally triggered run is inspected.
- Independent security review: NOT RECORDED.
- Parent PR #373 exact-head CI was pending at the start of this workstream; no predecessor CI evidence is transferred.

## Safety

Draft-only follow-up. No workflow retry/dispatch, merge, rebase, retarget, deployment, credentials, OAuth, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled.
