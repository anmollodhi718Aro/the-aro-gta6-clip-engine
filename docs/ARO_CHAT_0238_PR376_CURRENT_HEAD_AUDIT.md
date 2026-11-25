# ARO-CHAT-0238 | PR #376 current exact-head CI audit

Date: 2026-11-25

## Scope
Documentation-only audit of PR #376's current head, commit-associated Python CI, exposed job metadata, combined status, review state, and governing Issue #68 safety gate.

## Exact-head evidence
- PR: https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/376
- State at inspection: OPEN / DRAFT / UNMERGED.
- Head branch: `workstream/aro-chat-0238-ambiguous-numeric-hostname-rejection-2026-11-25`.
- Exact head: `33dc5cc461909bea41c21c361979ab9b1caae0e4`.
- Latest commit message: `docs: refresh ARO-CHAT-0238 startup handoff`.
- Associated Python CI run: https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45528776849 (run 1556).
- Run conclusion: FAILURE.
- Ubuntu job `138918585212` and hosted-Windows job `138918585633` both concluded FAILURE.
- The jobs endpoint exposed `steps: null` and `logs_url: null` for both jobs.
- Combined commit status returned zero status entries.
- The available evidence does not establish the failure phase or root cause. No compile, test, or test-count result is claimed. Do not attribute the failure to application code or tests.

## Review state
- PR review submissions: empty at inspection.
- Inline review threads: empty at inspection.
- Independent review: NOT RECORDED.
- Local repository tests in this connector session: NOT RUN.

## Bounded source review context
The PR patch includes fail-closed source-rights URL hostname validation:
- Numeric-like final hostname labels require the complete host to parse as canonical four-octet IPv4.
- Ambiguous shorthand/integer, malformed dotted, octal/hex-like, IDNA-normalized numeric-suffix, and scoped-IPv6-zone forms are covered by negative regression cases.
- Canonical IPv4, ordinary IPv6, and valid DNS/IDNA names have positive regression coverage.
- This is a bounded static description of the PR patch, not a complete security review or execution evidence.
- DNS resolution, destination-IP filtering, and DNS-rebinding protection are not implemented by this hostname helper and are not claimed.

## Governing security gate
Issue #68 remains OPEN / NOT IMPLEMENTED / WAITING_FOR_OWNER_APPROVAL. Its owner is UNASSIGNED. The authenticated channel-owner approval integration is still a separate P1 blocker. Keep live uploads and public publishing disabled.

## Disposition and safety
- Preserve PR #376 as OPEN / DRAFT / UNMERGED.
- Do not transfer CI evidence from earlier commits or sibling PRs.
- No workflow retry or manual dispatch was initiated.
- No source/test behavior, workflow configuration, OAuth, credentials, real media, upload, publishing, merge, rebase, retarget, deployment, or destructive action was performed.
- Next safe work remains bounded static review and evidence-based handoff. Any code change requires a narrowly scoped finding and must remain isolated from the Issue #68 owner-approval gate.


## Follow-up: digit-ending invalid numeric labels — 2026-11-25

- Static review found _ends_in_ipv4_number() accepted only valid hexadecimal-style labels beginning with 0x, decimal labels, and selected leading-zero decimal forms. It missed invalid numeric-looking labels that still end in an ASCII digit, such as 0xg1, abc1, and 0a9.
- URL parsers using the WHATWG “ends in a number” rule can classify a final label ending in an ASCII digit as an IPv4 candidate even when parsing that label as an IPv4 number fails. Such hosts must not fall through to ordinary DNS-label acceptance.
- Updated the helper to conservatively treat ASCII-digit-ending labels as numeric candidates, while retaining valid hexadecimal-prefix handling including the empty 0x suffix. The full hostname must still parse as canonical four-octet IPv4.
- Added negative regressions for example.0xg1, example.abc1, and example.0a9.
- Production commit: 50e007fe5567624a187a64e280ced3ba356dec86; test commit / current code-test head: 9a5956a88a075962980524cf126cad8fe2cbf0a0.
- Repository unit tests NOT RUN. Exact-head Ubuntu/hosted-Windows CI and independent review NOT YET VERIFIED / NOT RECORDED. This is a static finding and source/test edit, not execution evidence or a complete URL-parser security audit.
- No DNS resolution, destination-IP filtering, or DNS-rebinding protection is implemented or claimed. Preserve PR #376 DRAFT / OPEN / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled.
- No workflow retry/dispatch, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing was performed.
