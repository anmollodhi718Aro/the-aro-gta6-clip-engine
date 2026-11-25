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


### Post-fix CI evidence and exact-head recheck — 2026-11-25
- The production/test commit 9a5956a88a075962980524cf126cad8fe2cbf0a0 is associated with Python CI run #45531092780 (run 1560), conclusion FAILURE.
- Ubuntu job 138926286948 and hosted-Windows job 138926287425 both failed and exposed zero steps. Both job-log downloads returned BlobNotFound. Failure phase/root cause NOT VERIFIED; no compile or test result is established and failure is not attributed to application code.
- Combined commit status for the code/test commit returned zero status entries. Repository tests NOT RUN locally; independent review NOT RECORDED.
- After documentation synchronization, PR #376 exact head is 3118b6afdecd42a22f9aab229b4cb3a0b782cf1a. Commit-associated workflow lookup for that exact documentation head returned zero runs. Exact-head CI is PENDING / NOT VERIFIED; no CI evidence transfers from the code/test commit or earlier heads.
- PR #376 remains OPEN / DRAFT / UNMERGED. Issue #68 remains OPEN / NOT IMPLEMENTED / WAITING_FOR_OWNER_APPROVAL; owner UNASSIGNED. Keep live uploads/public publishing disabled.
- No workflow retry/dispatch, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing was performed.


### IDNA numeric compatibility-digit regression follow-up — 2026-11-25

- Static review enumerated Unicode characters accepted by Python's built-in IDNA codec that normalize to ASCII numeric suffixes. Existing tests covered superscript and single circled digits but did not cover subscript digits, mathematical styled digits, or multi-digit circled numerals.
- Added five test-only rejection cases: `example.₁`, `example.𝟙`, `example.⑩`, `example.㉑`, and `example.⁰`.
- An isolated probe using the current hostname-validation logic confirmed IDNA normalization to `example.1`, `example.1`, `example.10`, `example.21`, and `example.0`, respectively, and rejection of all five. This is not a repository unit-test run.
- Test commit: `1bc36c0d74cda85771c748801253a9fe0cb3e4c7`.
- Repository unit tests NOT RUN. Commit-associated exact-head CI lookup returned zero runs at the immediate post-commit check. Exact-head Ubuntu/hosted-Windows CI PENDING / NOT VERIFIED. Independent review NOT RECORDED.
- No production code, uploader, OAuth, media, workflow configuration, or publishing behavior changed. Preserve PR #376 DRAFT / OPEN / UNMERGED; Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled. No workflow retry/dispatch, merge, rebase, retarget, deployment, credentials, real media, upload, or publishing.


## Latest continuation audit — exact PR head 62d07a4b23d62bb2d73428abeaf5384a40df4146 (2026-11-25)

### Exact-head CI
- PR #376 current head at inspection: `62d07a4b23d62bb2d73428abeaf5384a40df4146`.
- Associated Python CI run #45537558568 (run 1570) completed FAILURE.
- Ubuntu job `138947788081` and hosted-Windows job `138947787726` both concluded FAILURE; the jobs endpoint exposed `steps: null` and `logs_url: null`.
- Failure phase and root cause are NOT VERIFIED. No compilation or test result is established. Do not attribute the failure to application code or tests.
- Local repository tests NOT RUN in this connector session. PR #376 review submissions and inline review threads remain empty; independent review NOT RECORDED.

### Bounded static review
- Re-inspected `backend/app/rights_registry.py` and `tests/test_rights_registry.py` at the current PR branch.
- The hostname helper now classifies any ASCII-digit-ending final label as an IPv4 candidate, including invalid hexadecimal-looking labels; empty `0x` suffixes are also treated as numeric candidates.
- The complete host must parse as canonical four-octet IPv4 when the final label is numeric-like. The code strips one terminal DNS dot before applying this rule.
- The regression matrix covers shorthand/integer, malformed dotted, octal/hex-like, numeric-ending DNS, trailing-dot, IDNA compatibility-digit, and scoped-IPv6-zone inputs, with positive canonical IPv4, ordinary IPv6, and DNS/IDNA controls.
- No additional concrete defect was identified in this bounded review of the hostname helper and listed cases. This is NOT a complete URL-parser, DNS-resolution, destination-IP, or DNS-rebinding security review.
- No repository tests were executed; static inspection is not test evidence.

### Disposition
- Preserve PR #376 OPEN / DRAFT / UNMERGED.
- Exact-head CI is FAILED / NOT VERIFIED; no compile/test result is claimed.
- Independent review remains NOT RECORDED.
- Issue #68 remains OPEN / NOT IMPLEMENTED / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
- No workflow retry/dispatch, source/test behavior change, OAuth, credentials, media, upload, publishing, merge, rebase, retarget, deployment, or destructive action was performed.
- Next safe step: obtain exact-head CI with visible job steps/logs through the normal workflow path and arrange independent review; do not retry/dispatch workflows without owner direction.


## Latest continuation audit — PR #376 exact head dc18af438161356266843edc04d7aceb7f9f72c0 (2026-11-25)

### Exact-head CI evidence
- Live PR metadata confirms PR #376 remains OPEN / DRAFT / UNMERGED on branch `workstream/aro-chat-0238-ambiguous-numeric-hostname-rejection-2026-11-25`.
- Exact PR head: `dc18af438161356266843edc04d7aceb7f9f72c0`.
- Commit-associated Python CI run [#45541566724](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45541566724), run 1577, completed FAILURE.
- Ubuntu job `138961085105` and hosted-Windows job `138961084835` both concluded FAILURE. The jobs endpoint exposed `steps: null` and `logs_url: null` for both.
- Combined commit status returned zero status entries. Failure phase/root cause NOT VERIFIED. No compile or test result is established; do not attribute the failure to application code or tests.
- Local repository tests NOT RUN in this connector session. PR #376 review submissions and inline review threads are empty; independent review NOT RECORDED.

### Bounded static review
- Re-read `backend/app/rights_registry.py` and `tests/test_rights_registry.py` from the active PR branch.
- Reviewed numeric-final-label detection, IDNA normalization, canonical IPv4 parsing, trailing-root-dot handling, percent rejection for scoped IPv6, and the regression test matrix.
- The current helper requires a complete canonical IPv4 parse whenever the normalized final label is numeric-like; ordinary DNS/IDNA and IPv6 paths remain represented by positive tests.
- No additional concrete defect was identified in this bounded hostname-validation review. This is not a full URL-parser differential, DNS-resolution, destination-IP, or DNS-rebinding review, and static inspection is not a test run.

### Disposition and next action
- Preserve PR #376 OPEN / DRAFT / UNMERGED. Do not transfer CI results from earlier heads.
- Exact-head CI is FAILED / NOT VERIFIED; root cause unknown. Local tests NOT RUN; independent review NOT RECORDED.
- Issue #68 remains OPEN / NOT IMPLEMENTED / WAITING_FOR_OWNER_APPROVAL; owner assignment/approval is still a separate gate. Keep live uploads and public publishing disabled.
- No workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, merge, rebase, retarget, deployment, or destructive action was performed.
- Next safe action: inspect a naturally triggered exact-head run only if it exposes meaningful job steps/logs, and obtain independent security review. Do not manually retry/dispatch workflows without owner direction.


## ARO-CHAT-0238 continuation: numeric-suffix over-rejection correction — 2026-11-25

- Static review of the current helper found an over-broad predicate: treating every final DNS label ending in an ASCII digit as an IPv4 candidate rejects ordinary DNS names such as `example.label1`, and malformed hex-like labels such as `0xg1` are not IPv4 numbers under the WHATWG IPv4-number parsing rules.
- Corrected `_ends_in_ipv4_number()` so it recognizes valid `0x`-prefixed hexadecimal forms and ASCII decimal-only labels, but does not classify arbitrary alphanumeric labels merely because their last character is a digit.
- Moved `example.0xg1`, `example.abc1`, and `example.0a9` from rejection cases into accepted DNS regression cases; added positive controls `example.label1` and `example.com1`.
- Production commit: `c9b621afc52b5b9ef84b459d6640b3fa1846fed6`; test commit: `f94c2d3d68084e6230fc10096605397fb9a145b6`.
- This is an implementation and test-source change only. Repository unit tests NOT RUN in this connector session; no test pass is claimed. Exact-head CI and independent review NOT VERIFIED / NOT RECORDED.
- Latest previously inspected exact PR head `77c05e767d198d19c82b4452dbf6cd6e6758d552` had Python CI run `45555803080` conclude FAILURE; Ubuntu and hosted-Windows jobs both exposed `steps: null` and `logs_url: null`. Failure phase/root cause NOT VERIFIED; no compile/test result is established and failure is not attributed to application code.
- Preserve PR #376 OPEN / DRAFT / UNMERGED. Issue #68 remains OPEN / NOT IMPLEMENTED / WAITING_FOR_OWNER_APPROVAL, owner UNASSIGNED. Keep live uploads/public publishing disabled.
- No workflow retry/dispatch, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing was performed.

### Exact commit-associated CI recheck after correction — 2026-11-25

- Production correction commit c9b621afc52b5b9ef84b459d6640b3fa1846fed6: associated workflow lookup returned zero runs and combined status returned zero entries.
- Regression-test commit f94c2d3d68084e6230fc10096605397fb9a145b6: Python CI run #45654439835 (run 1588) completed FAILURE. Ubuntu job 139347236120 and hosted-Windows job 139347235596 both exposed steps: null and logs_url: null.
- Documentation/current PR head 26339cda757d4571f39cd97d1c54d18898a66260: Python CI run #45654568414 (run 1590) completed FAILURE. Ubuntu job 139347667598 and hosted-Windows job 139347666996 both exposed steps: null and logs_url: null.
- Combined status returned zero entries for each inspected commit. Failure phase/root cause NOT VERIFIED; no compile or unit-test result is established. These failures are not attributed to application code.
- Repository tests NOT RUN locally. Independent review NOT RECORDED. PR #376 reviews and inline review threads were empty at inspection.
- PR #376 remains OPEN / DRAFT / UNMERGED. Issue #68 remains OPEN / NOT IMPLEMENTED / WAITING_FOR_OWNER_APPROVAL; owner UNASSIGNED. Keep live uploads/public publishing disabled.
- No workflow retry/dispatch, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing was performed.


## ARO-CHAT-0238 WHATWG numeric-suffix correction — 2026-11-25

- Standards reference: WHATWG URL Standard §3.5, especially the ends-in-a-number checker and IPv4 number parser. The checker returns true for all-ASCII-decimal final labels or labels successfully parsed as an IPv4 number. The latter includes `0x`-prefixed hexadecimal and leading-zero octal forms; arbitrary alphanumeric strings ending in digits are not numeric candidates.
- Concrete defect: `_ends_in_ipv4_number()` treated every ASCII-digit-ending label as numeric, rejecting valid DNS-style names such as `example.label1`, `example.abc1`, and `example.0a9`.
- Production fix commit: `f1e562824f2fd165249258bf454a2ad886c3255d`.
- Regression test commit: `019ccf37eb2afafa307584f86f8388630e9f0e03`. Positive cases now include ordinary alphanumeric labels; negative cases include decimal, octal, and hexadecimal suffix forms that must fail unless the full host is canonical IPv4.
- Focused isolated predicate probe passed 16 cases. This is not a repository test run. Repository unit tests NOT RUN; exact-head CI NOT VERIFIED; independent review NOT RECORDED.
- Keep PR #376 OPEN / DRAFT / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Live uploads/public publishing remain disabled. No workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, merge, rebase, retarget, or deployment was performed.


### ARO-CHAT-0238 exact-head CI recheck after WHATWG correction — 2026-11-25
- Current PR #376 head: `0dfa003c7cb923c6e034ee9608549d82a5ff00a2` (documentation synchronization after production/test commits).
- Python CI run #45668850752 (run 1624) completed FAILURE. Ubuntu job `139398317841` and hosted-Windows job `139398318523` both reported FAILURE; the jobs endpoint exposed `steps: []` and `logs_url: null`. Both log downloads returned `BlobNotFound`.
- Failure phase/root cause NOT VERIFIED. No compile or repository test result is established; failure is not attributed to the code or tests.
- The production commit `f1e562824f2fd165249258bf454a2ad886c3255d` and test commit `019ccf37eb2afafa307584f86f8388630e9f0e03` each also have naturally triggered Python CI runs #45668772916 and #45668788732, both concluded FAILURE. Their failures are not evidence of a source-code failure without exposed steps/logs.
- Exact-head workflow lookup returned run #45668850752; no workflow retry/dispatch was initiated. Repository unit tests NOT RUN. Focused isolated predicate probe passed 16 cases only. Independent review NOT RECORDED.
- Preserve PR #376 OPEN / DRAFT / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live uploads/public publishing disabled. No merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing.
