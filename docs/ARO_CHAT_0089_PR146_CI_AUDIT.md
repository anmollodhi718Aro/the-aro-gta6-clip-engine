# ARO-CHAT-0089 | PR #146 Merge-Ref CI Audit

**Date:** 2026-11-23  
**Chat ID:** ARO-CHAT-0089  
**Chat title:** ARO-CHAT-0089 | PR #146 Merge-Ref CI Audit  
**Workstream ID:** ARO-GTA-P0-89  
**Role:** Independent CI evidence auditor; documentation-only  
**Repository:** `anmollodhi718Aro/the-aro-gta6-clip-engine`

## Task

Audit the latest PR #146 CI evidence at its current head. Inspect both Ubuntu and hosted Windows jobs, decoded logs, test counts, synthetic media coverage, PowerShell validation, and the checkout ref. Do not change application, uploader, test, or workflow behavior.

## PR and branch state

- Parent PR: [#146](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/146)
- Parent PR title: Repair release-candidate pipeline CI failures
- Parent PR state at audit: OPEN / DRAFT / UNMERGED.
- Parent branch: `workstream/aro-pipeline-ci-repair-2026-11-23`
- Parent head SHA: `e3e1206d286a1e65d566b5820aa5529a8c5e472c`
- Parent base: `integration/release-candidate`
- Parent base SHA: `54cefb14c23b6d5d0bf9c1c6188ee1e9092cd70a`
- Audit branch: `workstream/aro-chat-0089-pr146-ci-audit-2026-11-23`
- Audit branch starting SHA: `6f9d184eb4447c64544ad93e05f7ad1708431e8e` (PR #143 head / common base before the duplicate ARO-CHAT-0088 submissions).
- Audit scope is documentation-only. No source, tests, uploader, workflow, or project configuration changes.

## Actions evidence

- Workflow: Python CI
- Run [#45230858696](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45230858696), run number 943, conclusion SUCCESS.
- The run is associated with PR #146 head `e3e1206d286a1e65d566b5820aa5529a8c5e472c`.
- Both jobs checked out `refs/remotes/pull/146/merge` at merge SHA `c8055145da4ac6f46aa017aba6658bf1f880eb75`, merging the PR head into base `54cefb14c23b6d5d0bf9c1c6188ee1e9092cd70a`.
- This is successful merge-ref CI evidence. A raw-head-only checkout was NOT demonstrated.

### Ubuntu

- Job `tests (ubuntu-latest)`, ID `137889693896`: SUCCESS.
- Source compilation step passed.
- FFmpeg installation step passed.
- The unittest step passed: `Ran 249 tests in 0.940s`.
- The generated synthetic-video render test `test_renders_a_generated_synthetic_video` passed as part of the suite.
- No Windows-only PowerShell validation was run on Ubuntu, as expected from the workflow conditions.

### Hosted Windows

- Job `tests (windows-latest)`, ID `137889694337`: SUCCESS.
- Source compilation step passed.
- FFmpeg/FFprobe installation completed; logs identify FFmpeg and FFprobe 9.1.
- The unittest step passed: `Ran 249 tests in 7.687s`.
- The generated synthetic-video render test `test_renders_a_generated_synthetic_video` passed as part of the suite.
- PowerShell parser validation for `scripts/check_project.ps1` and `scripts/manual_clip_wizard.ps1` passed.
- `scripts/check_project.ps1` completed successfully. It ran the project checks and a second unittest pass: `Ran 249 tests in 7.479s`.
- The Windows CI evidence is hosted-runner evidence, not an owner-device Windows smoke test.

## Interpretation and limits

- Run #943 passed on both required hosted platforms at the PR merge ref.
- Both primary unittest jobs ran the same 249-test suite; this is not 498 unique tests. Windows' local-check script additionally repeated the suite.
- Synthetic FFmpeg rendering is covered by the passing unit test. This run does not establish real GTA 6 media compatibility or first-real-clip acceptance.
- No real GTA 6 footage, third-party media, live OAuth session, network upload, or publishing was used.
- PR #146's body also references earlier run #942 at SHA `856e4d9c1afe299bac55176209a4bd87ce275240`; that is not the current PR head. Run #943 is the current-head-associated evidence and must be described as merge-ref CI, not raw-head CI.
- Local tests were not run in this connector session.

## Status

- PR #146 merge-ref CI: **CI_VERIFIED** on Ubuntu and hosted Windows.
- PR #146 raw-head-only CI: **NOT DEMONSTRATED**.
- Hosted Windows script validation: **CI_VERIFIED**.
- Owner-device Windows verification: **NOT RUN**.
- Real-media / first-clip acceptance: **NOT VERIFIED**.
- Parent PR #146 remains OPEN / DRAFT / UNMERGED. This audit does not authorize merge or release.

## Safety and reconciliation gates

- Issue #68 remains OPEN / UNASSIGNED. Keep live uploads and public publishing disabled until an implementation owner is assigned and a canonical authenticated-uploader implementation or explicit consolidation plan is approved.
- PRs #144 and #145 both claim ARO-CHAT-0088 / ARO-GTA-P1-88 and have divergent registry/startup snapshots. Preserve both PRs and branches; this workstream is based on their common predecessor and does not select either duplicate.
- PR #144's own head-associated run #45217116584 and PR #145's run #45205535343 both completed successfully on Ubuntu and hosted Windows, but both checked out their respective PR merge refs. This does not resolve the attribution collision.
- No credentials/tokens, OAuth session, real media, network upload, public publishing, merge, retarget, deployment, or destructive action was performed.
