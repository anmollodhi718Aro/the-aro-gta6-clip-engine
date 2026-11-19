# ARO Chat & Workstream Registry

**Purpose:** Durable, repository-visible attribution for AI-assisted engineering work. GitHub is the source of truth for changes; this file is an index, not proof that a task passed tests.

## Rules
1. Reserve one unique `ARO-CHAT-NNNN` ID and one `ARO-GTA-P0-NN` workstream ID before code changes.
2. One chat owns one active workstream at a time. Check this registry and open PRs before starting; do not duplicate active work.
3. Every AI-assisted PR must record Chat ID, exact chat title, Workstream ID, task, branch, base, starting SHA, changed files, commits, tests actually run, CI evidence, and status.
4. Use [ARO Chat Startup Prompt](ARO_CHAT_STARTUP_PROMPT.md) as the first instruction in every new AI engineering chat. Its first response line must suggest the chat title in the form `Suggested chat title: ARO-CHAT-NNNN | <short task title>`, then state IDs and proceed with work.
5. The first-line title is a cue for ChatGPT's automatic conversation-title behavior, not a guaranteed app control. This repository prompt cannot force or directly rename a ChatGPT conversation; the owner can rename it manually if automatic naming does not apply it.
6. Allocate IDs sequentially by checking this file and open PRs. Concurrent chats must reserve separately before coding; on collision, stop and request another ID.
7. A commit/branch/PR proves submission, not correctness. Only actual test logs and execution evidence justify VERIFIED states.
8. No merge, retarget, deploy, publish, or destructive action without owner approval.

## Status vocabulary
- `RESERVED`: ID allocated, no implementation evidence.
- `IN_PROGRESS`: work started.
- `IMPLEMENTED`: code/docs committed, tests not proven.
- `TESTED`: named tests executed with results.
- `CI_VERIFIED`: required CI passed on exact PR head SHA.
- `WINDOWS_VERIFIED`: owner-side Windows execution evidenced.
- `REAL_MEDIA_VERIFIED`: authorized real-media output generated and validated.
- `BLOCKED`: explicit blocker recorded.
- `COMPLETE`: acceptance criteria met with evidence.

## Registry

| Chat ID | Exact chat title | Workstream ID | Scope | Branch / PR | Status | Attribution evidence |
|---|---|---|---|---|---|---|
| ARO-CHAT-0001 | Legacy title not reliably recoverable | ARO-GTA-LEGACY-01 | Earlier MVP and clipping foundation; exact chat-to-PR mapping needs reconciliation | Multiple early PRs; no inferred ownership | HISTORICAL MAPPING UNVERIFIED | Reconcile PR descriptions and commit history before assigning |
| ARO-CHAT-0002 | CHAT-002: FFprobe Path Propagation and Output Validation | ARO-GTA-P0-05 | Propagate selected ffprobe through direct/batch rendering; validate MP4 metadata; add regression tests | `workstream/post-render-media-verification` / [PR #60](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/60) | IMPLEMENTED; tests, CI, Windows and real-media verification not established | PR #60 body contains Chat ID, workstream, commits, files and validation limits |
| ARO-CHAT-0003 | ARO-CHAT-0003: Chat and Workstream Attribution Registry | ARO-GTA-P0-06 | Add shared chat/workstream ledger and reusable startup identity/title prompt | `workstream/aro-chat-registry-2026-11-20` / [PR #63](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/63) | IMPLEMENTED; documentation-only; CI job failed before steps ran, so CI NOT VERIFIED | Commits `6c56634f87c3c871e07eef1717ae43d2e38cae8d`, `b08042b3a5b2eb7c334f994458ce2d8c43e4bd73`, `345ddf128751396c414622bbf90b4582ecf57c58`; files: this registry and [startup prompt](ARO_CHAT_STARTUP_PROMPT.md) |
| ARO-CHAT-0004 | ARO-CHAT-0004: Evidence-Based PR Consolidation Audit | ARO-GTA-P0-07 | Inspect open PR overlap, branch ancestry, CI evidence and RC divergence; document safe consolidation sequence | `workstream/pr-consolidation-audit-2026-11-20` / [PR #64](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/64) | IMPLEMENTED; CI and test verification blocked by Actions jobs with no exposed steps/logs | Commit `ed4c9664dc06232169cfdd09041e637e9af96b1d`; file `docs/PR_CONSOLIDATION_AUDIT.md`; no PRs merged, closed or retargeted |
| ARO-CHAT-0005 | ARO-CHAT-0005 | ARO-GTA-P0-08 | CI Recovery & First Real MP4 | ARO-GTA-P0-08 | Diagnose and recover CI execution; reconcile exact-head compile/unit-test evidence; then verify the authorized Windows manual clipping workflow and first valid FFprobe-checked 9:16 MP4 | `workstream/aro-chat-0005-ci-recovery-first-mp4-2026-11-20` / reservation branch; PR not yet created | RESERVED | Allocated after preserving existing CHAT-0003/P0-06 and CHAT-0004/P0-07 records; implementation and verification not yet claimed |

## New workstream entry template
| Chat ID | Exact title | Workstream ID | One bounded task | Branch / PR | Status | Evidence |
|---|---|---|---|---|---|---|
| ARO-CHAT-NNNN | Title | ARO-GTA-P0-NN | Task | branch / URL | RESERVED | Links |

## Latest audit notes
- GitHub may show the repository owner as author for multiple AI-assisted PRs. The GitHub account name alone cannot identify which ChatGPT conversation did the work.
- Reliable attribution is: Chat ID + Workstream ID in PR body → unique branch → commit SHAs → changed files → exact-head tests/CI evidence.
- Historical PRs without explicit attribution remain UNATTRIBUTED until evidence is added. Do not guess.
- The startup prompt asks for a title as the first response line to encourage automatic ChatGPT title generation. It cannot guarantee or directly control the app's title.
- PR #63's initial exact-head Python CI run failed with one job named `tests`, but the job reported `steps: []`, `runner_id: 0`, and no runner name. This is insufficient evidence of a test assertion failure; classify it as a CI/runner execution failure with test outcome unknown, not as passing.
- The registry is a static repository document, not yet an automatically maintained live dashboard. Future chats must update it with their own PR evidence.
