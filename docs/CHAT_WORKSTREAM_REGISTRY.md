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
| ARO-CHAT-0005 | ARO-CHAT-0005 \| CI Recovery and First Real MP4 | ARO-GTA-P0-08 | Diagnose CI execution and reconcile exact-head evidence; verify authorized Windows manual clipping and first FFprobe-checked 9:16 MP4 | `workstream/aro-chat-0005-ci-recovery-first-mp4-2026-11-20` / reservation branch; PR not created | IN_PROGRESS | OpenAI GPT-6 session; starting branch SHA `8d7ec91b27e04133e6b6cb26181404425acaef05`; live CI audit on 2026-11-20: run `44696785004` passed both Ubuntu and Windows jobs on SHA `817c7947c6756b80ae91ba272d172c3efaa2fa07`; latest PR #66 head `95c4cf6713c1de7fb19532f9230f1a919ca9439d` has run `44697208927` not yet complete, with FFmpeg installation cancelled and compile/tests skipped in both jobs; no app code changed or test claimed in this chat |

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


## ARO-CHAT-0005 live CI audit (2026-11-20)
- Chat title: `ARO-CHAT-0005 | CI Recovery and First Real MP4`; provider OpenAI; model GPT-6; workstream `ARO-GTA-P0-08`.
- Reused the pre-existing reservation branch `workstream/aro-chat-0005-ci-recovery-first-mp4-2026-11-20`; starting SHA `8d7ec91b27e04133e6b6cb26181404425acaef05`. No new branch or PR created.
- Current primary clipping integration remains PR #66 on `workstream/aro-zero-one-clipping-first-2026-11-20`; current observed head `95c4cf6713c1de7fb19532f9230f1a919ca9439d`. PR #67 is a separate owner-identity guard task; no overlapping source files were changed by this chat.
- CI run `44696785004` (run #728) passed both `tests` and `windows-tests` jobs on earlier PR #66 SHA `817c7947c6756b80ae91ba272d172c3efaa2fa07`; all compile and unit-test steps reported success. This is historical evidence for that exact earlier SHA only.
- Latest observed run `44697208927` (run #733) on SHA `95c4cf6713c1de7fb19532f9230f1a919ca9439d` has not established a pass: FFmpeg/FFprobe installation was cancelled in both jobs; compile and unit-test steps were skipped. Classify as infrastructure/setup interruption, not test assertion failure and not CI pass.
- Combined commit status for latest PR #66 head returned no status entries. Latest-head CI remains NOT VERIFIED.
- Windows-native behavior on an owner device and authorized GTA 6 real-media MP4/playback remain NOT VERIFIED. The owner-reported absence of GTA 6 recording means first real clip remains blocked pending an authorized media handoff.
- No source/test code changed, no PR created, no merge/retarget/deploy/upload/publishing performed. This entry records audit evidence only.

- Follow-up comparison: PR #66 implementation/tested SHA `817c7947c6756b80ae91ba272d172c3efaa2fa07` to current head `95c4cf6713c1de7fb19532f9230f1a919ca9439d` is 7 commits ahead and changes only `analytics/ai_chat_sessions.json`, `docs/ARO_MASTER_ANALYTICS_DASHBOARD.md`, `docs/ARO_PERMISSION_AND_APPROVAL_LEDGER.md`, `docs/CHAT_WORKSTREAM_REGISTRY.md`, and `docs/PROJECT_HANDOFF.md`; no application or test files changed. This supports carrying forward the earlier green source/test result as historical evidence for unchanged code, but does not convert the latest docs-only head into exact-head CI_VERIFIED.
