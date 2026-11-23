# ARO-CHAT-0091 | PR #147 Exact-Head CI Audit

**Date:** 2026-11-23  
**Chat ID:** ARO-CHAT-0091  
**Workstream ID:** ARO-GTA-P1-91  
**Role:** Exact-head CI evidence auditor; documentation-only  
**Repository:** `anmollodhi718Aro/the-aro-gta6-clip-engine`

## Task
Audit PR #147's exact-head Actions run, both Ubuntu and hosted Windows jobs, decoded logs, compile/test results, synthetic MP4/FFprobe validation, and checkout refs. Do not change application, uploader, test, or workflow behavior.

## Branch and ancestry
- Branch: `workstream/aro-chat-0091-pr147-exact-head-ci-audit-2026-11-23`
- Base branch: `workstream/aro-chat-0089-pr144-ci-closeout-2026-11-23`
- Starting SHA / PR #147 head: `06babec863840afb8cecf0dd6608021bce9067a1`
- Parent PR: [#147](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/147)
- Duplicate check: Chat ID ARO-CHAT-0091 and Workstream ARO-GTA-P1-91 were absent from the registry and open PR search; no matching branch reservation was found.
- ARO-CHAT-0090 was already reserved by another branch, so this task uses the next unused serial.

## Exact Actions evidence
- Workflow: **Python CI**
- Run [#45232862569](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45232862569), run number 945.
- Exact PR head: `06babec863840afb8cecf0dd6608021bce9067a1`
- Overall conclusion: **SUCCESS**.

### Ubuntu
- Job `tests`, ID `137896915549`: SUCCESS.
- FFmpeg/FFprobe installation, compilation, full unittest suite, and synthetic MP4/FFprobe validation completed successfully.
- Decoded log: `Ran 334 tests in 5.017s`.
- Checkout fetched and checked out `refs/remotes/pull/147/merge` at `759fe64c4362cd15cdc76b03fc7e85876aa152d4`.

### Hosted Windows
- Job `windows-tests`, ID `137896914783`: SUCCESS.
- FFmpeg/FFprobe installation, compilation, full unittest suite, and synthetic MP4/FFprobe validation completed successfully.
- Decoded log: `Ran 334 tests in 18.305s`.
- Checkout fetched and checked out `refs/remotes/pull/147/merge` at `759fe64c4362cd15cdc76b03fc7e85876aa152d4`.

## Interpretation and limits
- Both platforms ran the same 334-test suite; this is not 668 unique tests.
- Both jobs checked out the PR merge ref, not the raw PR head alone. Raw-head-only checkout is **NOT DEMONSTRATED**.
- Both synthetic reports state `gta6_footage_used=false`, `third_party_media_used=false`, `publishing_enabled=false`, and `manual_review_required=true`.
- Synthetic MP4/FFprobe success is not real GTA 6 media acceptance.
- Hosted Windows CI is not owner-device Windows verification.
- Local tests were not run in this connector session.

## Status
- PR #147 associated CI: **CI_VERIFIED on merge ref** (Ubuntu and hosted Windows, 334 tests each).
- Raw-head-only CI: **NOT DEMONSTRATED**.
- Owner-device Windows verification: **NOT VERIFIED**.
- Real-media / first real GTA 6 clip: **NOT VERIFIED**.
- This follow-up workstream: **CI_VERIFIED on PR merge ref** (run #45233266948; Ubuntu and hosted Windows, 334 tests each); raw-head-only CI is **NOT DEMONSTRATED**.

## Safety and owner gates
- PR #147 remains OPEN / DRAFT / UNMERGED; this audit does not authorize merge or integration.
- PR #146 is an independent open draft targeting `integration/release-candidate`; it was not modified.
- PR #144 remains the owner-selected canonical record for ARO-GTA-P1-88; PR #145 remains a preserved non-canonical alternate.
- Issue #68 remains OPEN / UNASSIGNED. Keep live uploads/public publishing disabled pending owner assignment and canonical authenticated-uploader implementation selection or approved consolidation.
- No credentials/tokens, OAuth session, real media, network upload, public publishing, merge, retarget, deployment, or destructive action was performed.


## Follow-up PR #150 CI evidence — 2026-11-23

- PR #150 head `5cb9e675b9b081bc1c45b55eaed1e3f470deddec` is associated with Actions run [#45233266948](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45233266948), run 948, conclusion SUCCESS.
- Ubuntu job `137898182465`: compile passed; decoded log reports `Ran 334 tests in 5.037s`; synthetic MP4/FFprobe validation passed.
- Hosted Windows job `137898183037`: compile passed; decoded log reports `Ran 334 tests in 12.176s`; synthetic MP4/FFprobe validation passed.
- Both jobs checked out `refs/remotes/pull/150/merge` at merge SHA `562731e4781719821418956d10d8cedf51a9cdea`, containing PR #150 head `5cb9e675b9b081bc1c45b55eaed1e3f470deddec`; raw-head-only checkout is not demonstrated.
- Both synthetic reports state `gta6_footage_used=false`, `third_party_media_used=false`, `publishing_enabled=false`, and `manual_review_required=true`.
- Both platforms ran the same 334-test suite, not 668 unique tests. Hosted Windows CI is not owner-device verification; synthetic media is not real GTA 6 media acceptance.
