# ARO-CHAT-0167 | PR #245 Exact-Head CI Audit

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0167
- Exact title: ARO-CHAT-0167 | PR #245 Exact-Head CI Audit
- Workstream ID: ARO-GTA-P1-167
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Role: Documentation-only exact-head CI auditor
- Branch: `workstream/aro-chat-0167-pr245-exact-head-ci-audit-2026-11-24`
- Base / starting SHA: PR #245 current head `d126b4bbb8f31c5b665703d707f89ab8f1e89bc1`
- Parent PR: [#245](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/245)

## Scope
Independently audit PR #245's current-head Actions run, both platform jobs and logs, checkout refs, compilation/tests, synthetic MP4/FFprobe validation, combined status, and review state. Documentation-only; no application or workflow behavior changes.

## Exact-head CI evidence
- PR #245 current head at reservation: `d126b4bbb8f31c5b665703d707f89ab8f1e89bc1`; base: `dfb1e9390490806e44bad93fc661ddff0a551f54`.
- Associated Python CI run [#45279564114](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45279564114), run 1126, completed SUCCESS.
- Ubuntu job #138060154970: compile passed; 340 tests passed (5.078s); synthetic MP4/FFprobe validation passed.
- Hosted-Windows job #138060154476: compile passed; the same 340 tests passed (14.902s); synthetic MP4/FFprobe validation passed.
- Both jobs checked out `refs/remotes/pull/245/merge` at merge SHA `c95a539627951d9ae0842b99c5ac641bbf6d5f86`, merging audited head `d126b4bbb8f31c5b665703d707f89ab8f1e89bc1` into base `dfb1e9390490806e44bad93fc661ddff0a551f54`. Raw-head-only checkout is NOT DEMONSTRATED.
- Count this as 340 shared test cases executed on two platforms, not 680 unique tests.
- Synthetic output on both platforms: locally generated test pattern/tone only; 8-second source, 4-second output; `gta6_footage_used=false`; `third_party_media_used=false`; `publishing_enabled=false`; `manual_review_required=true`. Mock approval output explicitly reports `upload_performed=false`; no live upload occurred.
- Run and both jobs concluded SUCCESS. Combined commit status returned zero entries; this is not an independent status check or reviewer approval.
- PR #245 review submissions, inline review threads, and conversation comments were empty. Independent review NOT RECORDED.
- PR #245 is OPEN / DRAFT / UNMERGED at inspection. This audit does not authorize merge or integration.

## Prior-head cancellation note
- An earlier run #45279416654 was cancelled on the earlier PR #245 head `594428bb4423410fd03cd12323b8d5e7de4223fa`; Windows unit tests were cancelled and synthetic rendering skipped, while Ubuntu completed. That run is not substituted for the current-head run #45279564114.
- Current PR #245 head advanced to `d126b4bbb8f31c5b665703d707f89ab8f1e89bc1`; the current-head run above is the evidence audited here.

## Safety and limitations
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL / UNASSIGNED. Keep live uploads and public publishing disabled pending owner approval, separate security review, owner-controlled integration, owner-device verification, and authorized real-media acceptance.
- Hosted-Windows CI is not owner-device Windows verification. Synthetic media is not GTA 6 footage and does not establish real-media acceptance.
- No credentials/tokens, OAuth action, real media, network upload, publishing, workflow retry, merge, rebase, retarget, deployment, or destructive action was performed.
- Local tests NOT RUN in this connector session. Draft only; no merge requested.

## Follow-up
Re-fetch PR #245's current head before any further status update. Any head change requires a fresh exact-head audit; do not transfer this run to a later head or another PR.
