# THE ARO | MASTER AI WORKFORCE & PROJECT ANALYTICS DASHBOARD

**Canonical dashboard specification and evidence snapshot**  
**Last live audit:** 2026-11-20 07:08 IST  
**Primary project:** THE ARO GTA 6 Clip Engine  
**Secondary project:** THE ARO Automation Deployment Beta

## Data integrity contract

Every metric must be labeled with one of:

- **VERIFIED:** Direct current evidence.
- **ESTIMATED:** Explicitly calculated from stated assumptions.
- **HISTORICAL:** Valid evidence from an earlier commit/run, not the current head.
- **UNAVAILABLE:** Data could not be retrieved.
- **NOT CONNECTED:** No verified connector/account is available.
- **NOT AUTHORIZED:** The action requires owner approval that is not present.
- **PENDING OWNER APPROVAL:** A specific owner decision is required.

Never invent durations, task totals, usage, scores, provider connections, permission grants, CI outcomes, or media readiness. Missing values remain `null` / N/A. A PR or commit is not proof of a passing implementation.

## Source-of-truth hierarchy

1. GitHub repository, branches, commits, PRs, issues, workflow runs, and job logs.
2. `docs/PROJECT_HANDOFF.md` for current architecture and delivery state.
3. `docs/CHAT_WORKSTREAM_REGISTRY.md` for chat identity and task ownership.
4. `analytics/ai_chat_sessions.json` for structured per-chat contribution evidence.
5. This dashboard for a readable synthesis, not a replacement for the underlying evidence.
6. Permission decisions in `docs/ARO_PERMISSION_AND_APPROVAL_LEDGER.md`.
7. Provider inventory in `docs/AI_PROVIDER_AND_MODEL_REGISTRY.md`.
8. Research findings in `docs/RESEARCH_REFERENCE_CATALOG.md`.

## A. Executive overview

| Metric | Value | Status | Evidence / note |
|---|---|---|---|
| Primary repository | `anmollodhi718Aro/the-aro-gta6-clip-engine` | VERIFIED | GitHub repository metadata |
| Default branch | `main` | VERIFIED | Repository metadata |
| Main SHA at audit | `5f3332770b27d8a5211b3e74feade222563a9263` | HISTORICAL SNAPSHOT | Recheck GitHub before any integration |
| Clipping workstream | ARO-ZERO-ONE, PR #66 | VERIFIED | Existing branch and PR reused |
| PR #66 state | Open, unmerged; targets `integration/release-candidate` | VERIFIED AT AUDIT | Live PR metadata; mergeable flag has varied and is not approval |
| PR #65 state | Open, unmerged; separate authorization foundation | VERIFIED AT AUDIT | Live PR metadata |
| Latest-head CI | Not established by the inspected cancelled run | UNAVAILABLE | Run 44655100375 cancelled during checkout; compile/tests skipped |
| Real authorized GTA 6 media | Not supplied | BLOCKED | Requires creator-authorized recording/export or supported media handoff |
| First authorized playable MP4 | Not verified | UNAVAILABLE | Synthetic output is not real GTA 6 footage |
| Production publishing | Not authorized | NOT AUTHORIZED | Requires separate owner approval |

## B. Project portfolio

| Project | Status | Verified progress | Last known milestone | Blocker | Next priority |
|---|---|---|---|---|---|
| THE ARO GTA 6 Clip Engine | ACTIVE / P0 | Manual clipping, FFmpeg renderer and FFprobe validation are present on the selected workstream; current-head CI must be reconciled | Local clipping-first renderer and synthetic validation | Authorized real GTA 6 recording/export and Windows playback evidence | Obtain authorized media, execute local render, inspect playback and record review state |
| THE ARO Automation Deployment Beta | PLANNED / P2 | No separate verified repository or deployment was identified in this audit | Scope defined in master project prompt | Existing repository identity and deployment target not verified | Keep paused until P0 clip milestone; verify existing repo before work |
| Other THE ARO projects | NOT REGISTERED HERE | N/A | N/A | No repository/task evidence in this audit | Register only after owner confirms scope |

Do not calculate an arbitrary progress percentage. Progress should be computed from approved acceptance criteria with evidence for each completed item.

## C. AI chat workforce

The structured source is `analytics/ai_chat_sessions.json`; the identity and ownership index is `docs/CHAT_WORKSTREAM_REGISTRY.md`.

| Chat ID | Workstream / focus | Status | Score | Evidence completeness |
|---|---|---|---|---|
| ARO-CHAT-0014 | Clipping-first execution and analytics foundation | Historical closeout | N/A | Historical record; metrics remain null where unmeasured |
| ARO-CHAT-0015 | Windows CI recovery and first-clip readiness | Historical / evidence limited | N/A | Windows dependency install failure recorded; no test execution claimed for that run |
| ARO-CHAT-0016 | Analytics schema integrity | Historical closeout | N/A | Focused checks reported; repository CI not verified by that session |
| ARO-CHAT-0017 | Research reference audit | Recorded in analytics ledger | N/A | Research catalog created; source review and CI status recorded separately |
| ARO-CHAT-0018 | Historical identity reconciliation | Historical | N/A | Duplicate attribution preserved; shared contribution not double-counted |
| ARO-CHAT-0019 | Analytics identity collision repair and exact-head CI recovery | In progress at latest registry snapshot | N/A | Do not infer final outcome from reservation or partial commits |
| ARO-CHAT-0020 | Governance ledgers and dashboard foundation | Active | N/A | Documentation task; no code tests claimed |

Do not infer active chat count from old registry entries. Count active sessions only from current, non-closed records in the structured ledger.

## D. AI leaderboard

**No leaderboard ranking is published yet.** The scoring model has changed across historical records and evidence completeness is uneven. Scores remain N/A until the scoring rubric is reconciled and sessions are closed.

Required separate leaderboards:

1. Overall contributor.
2. Coding.
3. Debugging.
4. QA.
5. Architecture.
6. Documentation.
7. Research.
8. Time efficiency.
9. Lowest regression rate.
10. Security compliance.

Each ranking must show sample size, task category, evidence completeness, confidence, and missing metrics. Use the documented weighted formula only after weights are reconciled with the current master prompt; never silently compare incompatible historical scores.

## E. Chat contribution history

For each session, retain task IDs, assigned scope, start/end timestamps, branch, starting/ending SHA, commits, PRs, changed files, tests actually run, CI run IDs, bugs found/fixed, regressions, blockers, owner approvals, and handoff. Unknown duration, usage, score, and counts remain null.

## F. Permissions and leadership

See `docs/ARO_PERMISSION_AND_APPROVAL_LEDGER.md`. THE ARO is the project owner. No separate project lead or maintainer grant was verified in this audit. GitHub API capability does not itself grant AI authority. Merge, deployment, publishing, secrets, destructive actions, and permission escalation remain owner-only.

## G. GitHub engineering activity

| Item | Status | Evidence / limitation |
|---|---|---|
| Main branch | HISTORICAL SNAPSHOT | SHA recorded above; recheck before integration |
| Integration branch | Exists | `integration/release-candidate` |
| Clipping branch | Exists | `workstream/aro-zero-one-clipping-first-2026-11-20` |
| PR #66 | Open, unmerged | Main clipping-first integration PR |
| PR #65 | Open, unmerged | Separate creator permission/approval foundation |
| PR #60 | Open in prior search; overlaps FFprobe validation | Do not merge overlapping implementations independently |
| Latest inspected workflow run | Cancelled before checkout/test steps | Run 44655100375; no compile/test conclusion |
| Merge / deployment / publication | Not performed by this audit | Owner approval required |

Reconcile all open/draft/closed/merged PRs and exact branch heads live before every integration decision. Do not rely on a cached PR count.

## H. Clipping production readiness

| Acceptance gate | Status | Evidence |
|---|---|---|
| Synthetic event analysis | HISTORICAL VERIFIED | Existing CLI/test records |
| Manual clip wizard | IMPLEMENTED on selected workstream | Existing project handoff |
| FFmpeg local renderer | IMPLEMENTED on selected workstream | Existing renderer code and tests |
| FFprobe output validation | IMPLEMENTED on selected workstream | Video stream, finite duration, duration tolerance and vertical dimensions checked before finalization |
| Synthetic FFmpeg render/decode | HISTORICAL VERIFIED | Earlier CI run 44633588158 reported 270 tests passed and synthetic MP4 render/probe/decode; not current-head proof |
| Current exact-head CI | UNAVAILABLE / PENDING | Latest inspected run cancelled before test steps |
| Windows owner-machine execution | NOT VERIFIED | Hosted Windows job is not the owner's laptop playback test |
| Creator rights confirmation | BLOCKED | Authorized GTA 6 recording/export not supplied |
| Real GTA 6 MP4 and playback | NOT VERIFIED | No real-media acceptance evidence |
| Persistent review dashboard/storage | NOT VERIFIED | Do not confuse an existing local review UI with durable production review storage |
| Publishing authorization | NOT AUTHORIZED | Separate per-upload owner approval required |
| Cloud workers / production hosting | NOT IMPLEMENTED | Later milestone |

## I. Automation Deployment Beta

See `docs/ARO_AUTOMATION_DEPLOYMENT_BETA.md`. Beta is deliberately secondary and paused until the first authorized clip milestone is achieved. No verified separate repository, deployment, workflow execution ledger, or production environment is claimed.

## J. Research intelligence

See `docs/RESEARCH_REFERENCE_CATALOG.md` for dated repository metadata, license review, files inspected, integration decisions and risks. Research findings are not implementation evidence. No external repository code should be copied or adopted without compatibility, license, and security review.

## K. Next execution priorities

1. Obtain an expressly authorized GTA 6 recording/export or supported creator media handoff.
2. Run the existing Windows/local workflow against a legal sample first, then authorized GTA 6 media when supplied.
3. Capture FFmpeg command/result, FFprobe metadata, decode/playback evidence and output hash.
4. Reconcile latest PR #66 head and exact-head CI logs; cancelled runs are not test failures or passes.
5. Resolve PR overlap and integration order with owner review; do not merge PRs automatically.
6. Implement durable review storage and enforce independent source and destination-channel permissions.
7. Keep public publishing manual and owner-approved.
8. Resume Automation Deployment Beta only after P0 clip acceptance.

## Update procedure

After every engineering session, update the structured analytics ledger and the relevant canonical docs. Record the exact commit SHA and CI run IDs. Refresh live GitHub facts before presenting a current dashboard. Do not overwrite historical evidence with current status or silently promote a prior CI pass to a newer commit.


## Live audit addendum — ARO-CHAT-0022 (2026-11-20 13:03 IST)

| Metric | Latest observation | Status | Evidence / limitation |
|---|---|---|---|
| Main branch | `5f3332770b27d8a5211b3e74feade222563a9263` | VERIFIED AT AUDIT | GitHub commit search and repository metadata |
| Active clipping PR | #66, open, unmerged, base `integration/release-candidate`, head observed `7c7979d04ecba5c9d6856ac2c0f6401045fbc70c` | VERIFIED AT AUDIT | Live PR metadata; no merge or retarget |
| Owner identity helper PR | #67, open, unmerged | VERIFIED AT AUDIT | PR body and head `000b8a63d52d1f4a48fabe65af867cf5a24868af` |
| PR #67 CI | Run `44655744416`; reported Ubuntu + Windows compile and 283 tests passed on tested SHA `c2d3dc1873a97d624dae78282d38448a0d54e3f6` | HISTORICAL / EXACT-SHA ONLY | PR body states later delta is analytics/docs only; do not transfer to later head without confirming diff |
| Authenticated uploader approval | Not integrated; issue #68 open and unassigned | NOT IMPLEMENTED | `youtube_upload.py` still accepts boolean CLI flags; helper identity comparison alone does not authenticate |
| Research catalog | Four priority references already catalogued under ARO-CHAT-0017 | VERIFIED AS DOCUMENTED | Re-read existing `docs/RESEARCH_REFERENCE_CATALOG.md`; no duplicate research record |
| First authorized GTA 6 MP4 | No authorized source media supplied | BLOCKED | Synthetic media tests cannot satisfy real-media acceptance |
| Windows owner-device playback | No owner-machine evidence in this audit | NOT VERIFIED | Hosted Windows CI is not owner-device playback |
| Automation Deployment Beta | No separate verified repository or deployment | NOT VERIFIED / PAUSED | P0 clipping milestone remains first |
| Current session | ARO-CHAT-0022, documentation/audit continuation | IN_PROGRESS | Registry, handoff and permission ledger updated on existing PR #66 branch; no code tests run |

### Current blocker and next priority
The highest-impact external blocker remains the missing creator-authorized recording/export/media handoff. The highest-impact engineering security gap is issue #68: bind verified OAuth channel identity to durable per-clip approval and recheck active permission immediately before upload. Do not enable public upload until that integration is tested and separately approved by the owner.


### ARO-CHAT-0022 exact-head CI reconciliation (2026-11-20)

- PR #66 latest observed head after this session's research-catalog update: `1f826cde5e8958885a024e27a307f57e278e077b`. PR remains open, non-draft, unmerged, targets `integration/release-candidate`, and GitHub reports mergeable.
- Docs-only commit `2e2ff9775367bf1856f894b62a7aafec3b5aa8f8` triggered Actions run `44696075728`; the run was cancelled during checkout. Both Ubuntu and Windows compile/test steps were skipped. Earlier documentation commits also triggered superseded cancelled runs. These are not test failures and not passing tests.
- The current latest PR #66 head `1f826cde5e8958885a024e27a307f57e278e077b` has no verified completed CI run in this audit. Mark latest-head CI NOT VERIFIED.
- PR #67 Actions run `44655744416` is VERIFIED successful at the workflow/job level: Windows and Ubuntu jobs both completed checkout, FFmpeg/FFprobe installation, compilation, and test steps. The PR body reports 283 tests passed on tested code/test SHA `c2d3dc1873a97d624dae78282d38448a0d54e3f6`. Its current PR head is `000b8a63d52d1f4a48fabe65af867cf5a24868af`; the current head status endpoint returned pending/no checks, so do not transfer the earlier run's result to that head without verifying the diff and run association.
- The owner-identity helper is not wired into `youtube_upload.py`; issue #68 remains open/unassigned. Actual upload remains unsafe to enable until the authenticated channel-owner + durable per-clip approval integration is completed and owner-approved.


## Live audit addendum — ARO-CHAT-0023 (2026-11-20 13:06 IST)

| Metric | Observation | Status | Evidence / limitation |
|---|---|---|---|
| Repository | `anmollodhi718Aro/the-aro-gta6-clip-engine` | VERIFIED | GitHub repository search/metadata |
| Default branch | `main` | VERIFIED | Repository metadata |
| Canonical docs | Present on existing ARO-ZERO-ONE workstream branch | VERIFIED | Direct file fetch; expected paths not found on main in initial fetch |
| Active clipping PR | #66, open/unmerged, base `integration/release-candidate` | VERIFIED AT AUDIT | Live PR search; exact current head SHA not established by available search result |
| Owner identity helper | PR #67, existing ARO-CHAT-0021 workstream | VERIFIED AT AUDIT | PR search and body; do not duplicate |
| Authenticated uploader approval | Issue #68 open/unassigned | VERIFIED | Issue body; implementation awaits owner assignment |
| Observed CI run | 44696106299, cancelled during FFmpeg/FFprobe installation on Ubuntu and Windows; compile/tests skipped | VERIFIED | Workflow run and job-step records for observed SHA `1f826cde5e8958885a024e27a307f57e278e077b` |
| Exact current PR #66 head CI | Not established | UNAVAILABLE | Observed SHA may not be latest PR head; do not transfer status |
| Real authorized GTA 6 MP4 | No authorized media supplied | BLOCKED | Requires creator-authorized recording/export or approved handoff |
| Research catalog | Existing, attributed to ARO-CHAT-0017 | VERIFIED AS DOCUMENTED | No duplicate research created |
| This chat | ARO-CHAT-0023, audit + docs-only reservation | IMPLEMENTED | No source/test/workflow code changes; 0 direct tests |

No leaderboard score is assigned: task completion, quality, and efficiency telemetry are incomplete. No merge, deployment, upload, or public publishing was performed.

## ARO-CHAT-0024 live audit snapshot — 2026-11-20

| Metric | Current observation | Status | Evidence / limitation |
|---|---|---|---|
| Default branch | `main` at `5f3332770b27d8a5211b3e74feade222563a9263` | VERIFIED AT AUDIT | GitHub repository metadata and PR base |
| PR #66 | Open, unmerged, non-draft; base `integration/release-candidate`; head `b718dc3c9ecacd040ee0c33a61491306d3293817` | VERIFIED | Live PR metadata |
| PR #66 latest-head CI | Run `44696524352` cancelled; no job records; zero commit checks | NOT VERIFIED | Exact-head workflow and commit status endpoints |
| Earlier Windows CI | Run `44696171430` completed Windows compile and unit-test steps on SHA `56a1c573093937ebd7b49b1c5e383990d8fff83f` | HISTORICAL | Ubuntu cancelled during FFmpeg/FFprobe install; not exact latest head |
| Chat serial collision | Two registry reservations for ARO-CHAT-0023; one structured analytics record | VERIFIED | Registry and analytics ledger inspected; historical ownership unresolved |
| ARO-CHAT-0024 | Read-only QA/audit closeout | IMPLEMENTED | Registry/handoff/permission/dashboard/analytics record; no code changes |
| Issue #68 | Open and unassigned; owner assignment required | VERIFIED / PENDING OWNER APPROVAL | Issue body explicitly reserves implementation assignment to project owner |
| First authorized GTA 6 MP4 | No authorized media handoff supplied | BLOCKED | Synthetic fixture output is not real-media acceptance |
| Research catalog | Existing, attributed to ARO-CHAT-0017 | VERIFIED AS DOCUMENTED | Reused; no duplicate research |
| Automation Deployment Beta | Planned; no separate verified repository/deployment | HISTORICAL / NOT VERIFIED | Remains paused below P0 clipping milestone |

No numerical workforce score is assigned to ARO-CHAT-0024: task completion, time and independent test telemetry are incomplete. No arbitrary progress percentage is reported.


## ARO-CHAT-0026 exact-head CI snapshot — 2026-11-20 13:11 IST

| Metric | Observation | Status | Evidence / limitation |
|---|---|---|---|
| PR #66 head | `817c7947c6756b80ae91ba272d172c3efaa2fa07` | VERIFIED | Live PR metadata and workflow run |
| Ubuntu CI | Compile + 281 unit tests passed | CI PASSED | Job `136155337178`, run `44696785004` |
| Windows CI | Compile + 281 unit tests passed | CI PASSED | Job `136155337553`, run `44696785004` |
| Combined test executions | 562 across two platforms; 281 distinct test cases | VERIFIED | Both job logs report `Ran 281 tests` and `OK` |
| ResourceWarning | Non-fatal Python ResourceWarning observed | INFORMATIONAL | Does not change successful job conclusions; low-priority test hygiene |
| Owner-device Windows execution | Not performed | UNVERIFIED | Hosted Windows CI is not owner-device verification |
| Authorized GTA 6 MP4 | No authorized recording/export supplied | BLOCKED | Synthetic media does not satisfy real-media acceptance |
| Issue #26 | Exact-head CI evidence comment added | VERIFIED | Comment `7033585164` |
| ARO-CHAT-0026 | Read-only QA and documentation update | IMPLEMENTED | No application/test/workflow code changes; no direct local tests |

No workforce score is assigned: independent time-efficiency and broader quality telemetry are insufficient. PR #66 remains open and unmerged. No deployment, upload, or public publishing was performed.


## ARO-CHAT-0028 live audit snapshot — 2026-11-20 13:14 IST

| Metric | Observation | Status | Evidence / limitation |
|---|---|---|---|
| PR #66 tested code SHA | `817c7947c6756b80ae91ba272d172c3efaa2fa07` | VERIFIED | Actions run `44696785004`; audited renderer/uploader/test file blobs match this SHA |
| Ubuntu CI | 281 unit tests passed; compile and FFmpeg/FFprobe setup passed | CI PASSED | Job `136155337178`; prior chat ARO-CHAT-0026 executed the run |
| Windows hosted CI | 281 unit tests passed; compile and FFmpeg/FFprobe setup passed | CI PASSED | Job `136155337553`; hosted runner only, not owner-device execution |
| Distinct test count | 281; executed independently on two platforms | VERIFIED | 562 successful executions are not 562 distinct test cases |
| Test hygiene | Unclosed-file ResourceWarning at `tests/test_batch_render.py:227` | VERIFIED / LOW | Non-failing warning on Ubuntu and Windows; not fixed in this audit |
| Current PR #66 branch-tip SHA | Not exposed by available connector results | UNAVAILABLE | Do not claim the unknown latest branch tip is CI-verified |
| PR #67 | Owner-identity equality helper remains separate | VERIFIED AT AUDIT | Does not authenticate the OAuth principal or wire into the uploader |
| Issue #68 | OPEN / UNASSIGNED | PENDING OWNER APPROVAL | Owner must assign/approve implementation owner; public upload remains disabled |
| PR #69 | Review-dashboard no-overwrite workstream | VERIFIED AT AUDIT | Separate workstream; ARO-CHAT-0027 already reserved its QA branch |
| Research catalog | Four priority references and license notes already documented | VERIFIED AS DOCUMENTED | Reused ARO-CHAT-0017 / ARO-CHAT-0022 records; no duplicate research |
| Automation Deployment Beta repository | No separate repository found in connected account inventory | UNAVAILABLE | Only the GTA 6 Clip Engine repository was returned; Beta remains planned/paused |
| First authorized GTA 6 MP4 | No authorized recording/export supplied | BLOCKED | Synthetic fixtures and CI do not prove real-media compatibility |
| ARO-CHAT-0028 | Live audit and documentation reconciliation; no application/test code changes | IMPLEMENTED | Direct local tests: 0; no numerical workforce score assigned due incomplete time/quality telemetry |

No merge, retarget, deployment, upload, public publishing, or issue #68 implementation was performed. The exact CI evidence above belongs to SHA `817c7947c6756b80ae91ba272d172c3efaa2fa07`, not to an unknown later branch tip.


## ARO-CHAT-0030 live execution snapshot — 2026-11-20

| Metric | Observation | Status | Evidence / limitation |
|---|---|---|---|
| Chat ID / workstream | ARO-CHAT-0030 / ARO-GTA-P0-30 | VERIFIED | Canonical registry and PR #71 |
| Implementation PR | [#71](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/71), OPEN / DRAFT / UNMERGED | VERIFIED | Stacked on existing PR #66; no merge or retarget |
| Branch head | `bb71afc5b4c7b9d37440d5e7e85643dd28995b7c` | VERIFIED | GitHub branch ref and PR metadata |
| Audio stream requirement | Optional validator/renderer/CLI gate; Windows wizard defaults to requiring audio | IMPLEMENTED | Source diff and regression tests in PR #71 |
| CI | Run `44700696502`; Ubuntu and Windows hosted jobs succeeded | CI PASSED | Both compile and unit-test steps completed on exact head; test count not recovered |
| Direct local tests | 0 | VERIFIED | No local execution environment exposed through this connector session |
| Owner-device Windows execution | Not performed | NOT VERIFIED | Hosted Windows CI is not owner-device evidence |
| Authorized GTA 6 media | Not supplied | BLOCKED | No creator-authorized recording/export or supported handoff |
| First actual playable GTA 6 MP4 | Not produced | NOT VERIFIED | Synthetic CI does not satisfy real-media acceptance |
| Public publishing | Not authorized | NOT AUTHORIZED | Separate per-clip and channel approval required |
| Workforce score | `null` / provisional | UNAVAILABLE | Session timing and normalized category telemetry are incomplete |

### ARO-CHAT-0030 contribution summary

- Implemented an explicit FFprobe audio-stream acceptance gate with backward-compatible default behavior.
- Added three regression tests and updated the Windows first-clip wizard and manual clipping guide.
- Eight code/test/script/documentation commits; PR #71 contains the implementation.
- No numerical leaderboard score assigned. No direct local tests; CI is the verification evidence.
- Reservation sequencing deviation: the initial code commits preceded the registry update. This is disclosed in the canonical registry and PR body.


## ARO-CHAT-0031 live execution snapshot — 2026-11-20

| Metric | Observation | Status | Evidence / limitation |
|---|---|---|---|
| Chat / task | ARO-CHAT-0031 / ARO-GTA-P2-31 | VERIFIED | Canonical registry and PR #73 |
| Scope | Close the CSV reader in one batch-render test | IMPLEMENTED | Context manager in `tests/test_batch_render.py` |
| PR | [#73](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/73) | OPEN / DRAFT / UNMERGED | Stacked on PR #71 workstream branch |
| Direct local tests | 0 | NOT RUN | No local Python test runtime used |
| Exact-head CI | No run | NOT VERIFIED | Existing pull_request filter targets `main`; stacked base is not `main` |
| Parent baseline | 284 tests passed on Ubuntu and 284 on Windows | VERIFIED FOR PARENT ONLY | Run 44700987089 on parent SHA `4787c069d498b51177968546198eea3e1e8ac84a`; not evidence for PR #73 |
| Workforce score | N/A | INSUFFICIENT EVIDENCE | Active time and exact-head test evidence incomplete |
| First authorized GTA 6 MP4 | Not produced | BLOCKED | Authorized recording/export still required |
