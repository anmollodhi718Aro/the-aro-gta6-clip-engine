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


## Follow-up: leading-zero numeric suffixes — 2026-11-25

- Static review found that the initial suffix classifier recognized leading-zero labels only when every remaining digit was octal (`0`–`7`). A label such as `09` therefore fell through to ordinary DNS-label validation.
- Updated `_ends_in_ipv4_number()` to conservatively classify every all-decimal label beginning with zero as numeric-like. Such a suffix is accepted only if the complete hostname parses as canonical four-octet IPv4.
- Added URL rejection regressions for `example.09` and `example.0008`.
- Production commit: `8d9812d8c88ad4549e5677a4a3a175b4e75bdd26`; test commit / current branch head: `f6bb501eccf77445509f85e24ec69babbd61e41a`.
- Commit-associated workflow lookup for the current head returned zero runs. Exact-head CI: PENDING / NOT VERIFIED. Local tests NOT RUN. Independent review NOT RECORDED.
- PR #376 remains draft/open/unmerged. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled.


### Trailing-dot numeric-host regression follow-up — 2026-11-25

- Test-only commit `4cde1bb1b12ab95fd9779171f95d93f78621760e` adds rejection cases for numeric-like DNS suffixes with a trailing dot (`example.123.`, `example.0x2.`, `example.09.`) and a positive canonical IPv4 trailing-dot case (`192.0.2.1.`).
- Production behavior is unchanged. The existing validator strips one terminal DNS dot before applying the numeric-suffix/canonical-IPv4 rule.
- Local tests NOT RUN in this connector session. Exact-head Ubuntu/hosted-Windows CI NOT YET CHECKED for the new commit. Independent security review NOT RECORDED.
- PR #376 remains DRAFT / OPEN / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.


## Exact-head CI recheck — 2026-11-25

- Audited commit `4cde1bb1b12ab95fd9779171f95d93f78621760e`, the trailing-dot regression test commit.
- Associated Python CI run [#45506152240](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45506152240) completed FAILURE.
- Ubuntu job `138841778044` and hosted-Windows job `138841778291` both completed FAILURE and exposed zero workflow steps. Both job-log downloads returned `BlobNotFound`.
- Failure phase/root cause NOT VERIFIED. The available evidence does not establish whether the jobs failed during runner/workflow initialization or before the first step. Do not attribute the failure to application code or tests.
- Local repository tests NOT RUN in this connector session. No compile or test count is claimed. Exact-head CI is FAILED / NOT VERIFIED. Independent security review NOT RECORDED; PR #376 review submissions and inline threads were empty at inspection.
- No workflow retry/dispatch was initiated. PR #376 remains DRAFT / OPEN / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
- No source code, test behavior, uploader, OAuth, media, workflow configuration, merge, rebase, retarget, deployment, upload, or publishing behavior was changed during this audit.


### Scoped IPv6 zone-identifier rejection follow-up — 2026-11-25

- Static comparison with the current strict-hostname policy found this branch still accepted scoped IPv6 URL hostnames because Python's `ipaddress.IPv6Address` accepts zone identifiers.
- Production change: `_valid_hostname()` now rejects any percent sign in the parsed hostname before IPv6 parsing. Scoped IPv6 zone identifiers are unsupported at this registry boundary; ordinary IPv6 literals remain accepted.
- Added negative regressions for URI-encoded `%25` and raw `%` zone delimiters.
- Production commit: `7306d114dc50bbfe79d5ef2699b3df907f871e04`; test commit: `475a55732d710332a2751c0012c780b75f081ed3`.
- Local repository tests NOT RUN. Exact-head Ubuntu/hosted-Windows CI NOT YET CHECKED for this code/test head. Independent security review NOT RECORDED.
- This is a fail-closed source-rights URL validation change only; no DNS resolution, destination-IP policy, uploader, OAuth, media, workflow configuration, or publishing behavior changed.
- Preserve PR #376 DRAFT / OPEN / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Do not retry/dispatch workflows without owner direction; keep live uploads/public publishing disabled.
