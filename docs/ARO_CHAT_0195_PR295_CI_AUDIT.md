# ARO-CHAT-0195 | PR #295 exact-head CI audit

- Chat ID: ARO-CHAT-0195
- Exact chat title: ARO-CHAT-0195 | PR #295 Exact-Head CI Audit
- Workstream ID: ARO-GTA-P1-195
- Role: Documentation-only independent exact-head CI auditor
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Audited PR: #295, [Add isolated destination profiles for private uploads](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/295)
- Audited head: `cf731cabda8a045d39457f0eef800dbdb051e75e`
- Audit branch: `workstream/aro-chat-0195-pr295-exact-head-ci-audit-2026-11-24`
- Base / starting SHA: PR #295 head `cf731cabda8a045d39457f0eef800dbdb051e75e`

## Scope

Independently inspect PR #295's commit-associated Actions run, Ubuntu and hosted-Windows jobs, checkout refs, compilation, tests, synthetic MP4/FFprobe validation, combined status, and review state. Record observed evidence only. Do not modify the implementation under audit.

## Initial exact-head evidence

- PR #295's current REST head is `cf731cabda8a045d39457f0eef800dbdb051e75e`; its base is `4e01f16e97b2239c74a2f96c4262b04b57a4ae73`.
- Exact-head workflow run #45390003956 (run 1233) is associated with audited head `cf731cabda8a045d39457f0eef800dbdb051e75e`.
- Ubuntu job #138430897019 completed SUCCESS: source compilation, unit tests, and synthetic MP4 render/FFprobe steps succeeded.
- Hosted-Windows job #138430897645 was still IN_PROGRESS at initial inspection. Compilation succeeded; the complete unittest suite was running. Windows test/render outcome is NOT YET VERIFIED.
- Combined status for the exact head returned `pending` with zero legacy status entries. This is not a passing signal.
- A prior run #45388115805 (run 1230) failed on a different PR merge SHA `c767f8110049abfaebce62950c293d2afb0fe8b9`; do not transfer that result to the current PR head or treat it as the current exact-head result.
- PR #295 review submissions were empty at inspection; independent review NOT RECORDED.
- PR #295 is OPEN / DRAFT / UNMERGED.

## Implementation under audit

PR #295 adds local destination profiles with distinct Google OIDC subjects, YouTube channel IDs, and profile-specific token paths; profile names are constrained, duplicate channel mappings fail closed, and a profile token override is rejected. Metadata dry-runs remain independent of OAuth. Tests use synthetic fixtures. This audit does not certify the implementation's security correctness.

## Safety boundaries

- Documentation-only. Do not change uploader, application, tests, renderer, media-ingestion, or workflow behavior under audit.
- No OAuth login, credentials/tokens, real media, network upload, publishing, workflow retry, merge, rebase, retarget, deployment, or destructive action.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
- Synthetic media is not GTA 6 footage or real-media acceptance. Hosted Windows is not owner-device Windows verification.
- Do not claim CI_VERIFIED until both jobs on this exact head finish successfully and checkout refs/logs are reviewed. Do not transfer results from any other SHA.

## Status

IN_PROGRESS. Ubuntu exact-head job passed; hosted-Windows exact-head job pending at initial inspection. Final closeout requires re-fetching the run, both jobs/logs, checkout refs, combined status, and review/comment collections.


## Exact-head CI closeout — 2026-11-24

- PR #295 exact head `cf731cabda8a045d39457f0eef800dbdb051e75e` completed run [#45390003956](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45390003956) (run 1233) with conclusion SUCCESS.
- Ubuntu job #138430897019 and hosted-Windows job #138430897645 both passed source compilation, the same 331-test unittest suite, and synthetic MP4 render/FFprobe validation. Test durations were 4.967s Ubuntu and 13.868s Windows. This is 331 shared tests on two hosted platforms, not 662 unique tests.
- Both jobs checked out PR #295 merge ref at merge SHA `0568fdb4b4453f97bbd51e639343dd0f1d9aea5d`, merging audited head `cf731cabda8a045d39457f0eef800dbdb051e75e` into base `4e01f16e97b2239c74a2f96c4262b04b57a4ae73`. Raw-head-only checkout is NOT DEMONSTRATED.
- Synthetic evidence only: logs report `gta6_footage_used=false`, `third_party_media_used=false`, `publishing_enabled=false`, `manual_review_required=true`, and mocked `upload_performed=false`.
- Combined status remains `pending` with zero legacy status entries. The Actions run is green, but no separate legacy status context was reported.
- PR #295 review submissions, inline review comments, and conversation comments were empty at inspection; independent review NOT RECORDED. PR #295 remains OPEN / DRAFT / UNMERGED.
- Owner-device Windows and authorized real-media acceptance remain NOT VERIFIED. No workflow retry, OAuth, credentials, real media, network upload, publishing, merge, rebase, retarget, deployment, or destructive action occurred.
- Final audit status: CI_VERIFIED for PR #295's exact-head-associated merge-ref run on hosted Ubuntu and Windows; independent review NOT RECORDED.
