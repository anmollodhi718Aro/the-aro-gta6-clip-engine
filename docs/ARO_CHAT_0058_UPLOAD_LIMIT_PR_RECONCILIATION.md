# ARO-CHAT-0059: Upload-Limit PR Reconciliation

Date: 2026-11-23

## Scope

Bounded, read-only reconciliation of the overlapping ARO-CHAT-0058 upload-limit regression submissions (#106, #107, #108, and #109), including exact-head GitHub Actions evidence. This document does not select an implementation PR, authorize integration, or change uploader behavior.

## Findings

All four pull requests identify the same Chat ID (ARO-CHAT-0058) and Workstream ID (ARO-GTA-P1-58), but use different branches and, in some cases, different bases. They overlap on the cumulative multi-read size-limit regression:

| PR | Base | Test scope observed | Exact-head CI |
|---|---|---|---|
| [#106](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/106) | PR #105 review branch | Multi-read helper test; integrated upload-copy growth test with staging cleanup and no API insert; direct-call oversize guard before OAuth/API/media setup | Run [45104569746](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45104569746), Ubuntu + hosted Windows successful; 334 tests on each platform |
| [#107](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/107) | PR #105 review branch | Multi-read helper test only; relies on direct-call guard already in its ancestry | Run [45104584626](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45104584626), Ubuntu + hosted Windows successful |
| [#108](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/108) | Earlier PR #45 workstream | Multi-read helper test only; body references a separate direct-call guard in PR #96 lineage | Run [45104575778](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45104575778), Ubuntu + hosted Windows successful |
| [#109](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/109) | PR #105 review branch | New focused test module: multi-read helper test and direct-call oversize guard before Google client/media/OAuth setup; does not include the integrated upload-copy growth/staging-cleanup regression present in #106 | Run [45104624957](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45104624957), Ubuntu + hosted Windows successful; 334 tests on each platform |

## Assessment

1. The registry's earlier ARO-CHAT-0058 entry was still marked as awaiting test execution and exact-head CI. That status is superseded for PR #106 and PR #109 by the exact-head successful runs above. PR #107 and #108 also have successful exact-head CI runs.
2. PR #106 has the broadest directly observed regression coverage of the identified gaps because it exercises the helper's cumulative limit, the upload-path growth/staging cleanup behavior, and the direct-call fail-fast guard.
3. PR #109 independently covers the helper and direct-call guard in a separate test module, but does not contain the integrated upload-path growth regression. It is not a reason to integrate a second copy of the same test scope.
4. PR #107 and #108 are narrower overlapping variants. Their successful CI is useful evidence for their exact heads, not a reason to merge all parallel variants.
5. This is a bounded patch/CI comparison, not an exhaustive code review or security sign-off. No conclusion is made about real-world upload safety.

## Required disposition

- Preserve all PRs and their ancestry until the project owner or assigned implementation owner selects a canonical test branch or explicitly approves a consolidation plan.
- Do not merge #106, #107, #108, or #109 independently into overlapping bases.
- If the owner chooses to consolidate, retain the integrated upload-path growth regression from #106 and avoid duplicating equivalent helper/direct-call tests unless the selected base lacks them.
- Issue #68 remains OPEN / UNASSIGNED. This audit does not select the canonical authenticated-uploader implementation.
- Keep live uploads and public publishing disabled pending owner-controlled security selection, independent review, and the remaining source-rights, approval, device-limit, and real-media gates.

## Boundaries

No uploader/application behavior, OAuth credentials, tokens, live OAuth session, real media, network upload, public publishing, merge, retarget, deployment, or destructive action was performed. The reviewed CI uses synthetic test data and synthetic MP4 output only. Hosted Windows CI is not owner-device Windows verification.
