# ARO-CHAT-0121 | PR #191 Exact-Head CI Audit

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0121
- Exact title: ARO-CHAT-0121 | PR #191 Exact-Head CI Audit
- Workstream ID: ARO-GTA-P1-121
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0121-pr191-exact-head-ci-audit-2026-11-24`
- Base / starting SHA: PR #191 head `35d77ce48ec6fbd2f86503a3f45f3ba88d325efc`
- Parent PR: #191, testing the ARO-CHAT-0120 test-contract correction for PR #176

## Scope
Audit only PR #191's own commit-associated Actions run, both hosted jobs, compile/test/synthetic-render steps, checkout refs, combined status, and review records. Documentation-only; no uploader or parent implementation changes.

## Exact-head Actions evidence
- PR #191 head `35d77ce48ec6fbd2f86503a3f45f3ba88d325efc` is associated with Python CI run [#45256856022](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45256856022), run 1015, conclusion SUCCESS.
- Ubuntu job #137980832512: compile passed; 338 tests passed in 4.965s; synthetic MP4/FFprobe validation passed.
- Hosted-Windows job #137980833158: compile passed; 338 tests passed in 14.816s; synthetic MP4/FFprobe validation passed.
- Both jobs checked out `refs/remotes/pull/191/merge` at merge SHA `811195d53fa14c7a54d892204ae056b8bac286ac`, merging audited PR #191 head into base `2a83ce65706d0a8ccce0d5eaf56651fb9f5caa69`. Raw-head-only checkout is NOT DEMONSTRATED.
- Both platforms ran the same 338-test suite, not 676 unique tests.
- Synthetic reports on both platforms show a locally generated test pattern/tone, source duration 8.0 seconds, rendered duration 4.0 seconds, `gta6_footage_used=false`, `third_party_media_used=false`, `publishing_enabled=false`, and `manual_review_required=true`.
- Logs include non-failing Node.js 20 deprecation warnings for actions/checkout@v4 and actions/setup-python@v5 under Node.js 24; this audit does not change workflow configuration.
- The run-level Actions conclusion is SUCCESS. The legacy combined-status endpoint still returned PENDING with zero status entries; no separate legacy status was available. Do not confuse that empty status list with a failed test job.

## Review and verification status
- PR #191 review submissions: empty at inspection.
- PR #191 inline review comments: empty at inspection.
- Local tests: NOT RUN in this connector session.
- Exact-head CI: CI_VERIFIED on the PR merge ref, not on a demonstrated raw-head-only checkout.
- Independent review: PENDING / NOT RECORDED.
- Hosted Windows CI is not owner-device Windows verification. Synthetic media is not real GTA 6 footage and does not satisfy real-media acceptance.

## Safety and owner gates
- Documentation-only audit. No application, uploader, test, or workflow behavior changes.
- No credentials/tokens, OAuth session, real media, network upload, public publishing, merge, retarget, deployment, or destructive action.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled until the owner-controlled security gates and integration approval are satisfied.
