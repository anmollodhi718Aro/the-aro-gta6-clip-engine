# ARO Chat & Workstream Registry

**Purpose:** Durable, repository-visible attribution for AI-assisted engineering work. GitHub is the source of truth for changes; this file is an index, not proof that a task passed tests.

## Rules

1. Reserve one unique `ARO-CHAT-NNNN` ID and one `ARO-GTA-P0-NN` workstream ID before making code changes.
2. One chat owns one active workstream at a time. Check this registry and open PRs before starting; do not duplicate an active owner/task.
3. Every AI-authored PR must include these fields in its description: Chat ID, exact chat title (as supplied by the owner), Workstream ID, task, branch, base branch, starting SHA, changed files, commits, tests actually run, CI evidence, and completion state.
4. Keep attribution in the PR body and add the PR URL/status to this registry after the PR exists. Never claim a chat title was changed automatically: the GitHub connector cannot rename ChatGPT conversations.
5. IDs are allocated sequentially by checking this file and open PRs. Concurrent chats must reserve IDs through separate registry PRs before coding; if a collision occurs, stop and request a new ID.
6. A commit, branch, or PR proves a change was submitted, not that it works. Only test logs and real execution evidence justify VERIFIED states.
7. Never merge, retarget, deploy, publish, or perform destructive actions without explicit owner approval.

## Status vocabulary

- `RESERVED`: ID allocated, no implementation evidence yet.
- `IN_PROGRESS`: work has started.
- `IMPLEMENTED`: code/docs committed, tests not yet proven.
- `TESTED`: named tests executed with recorded results.
- `CI_VERIFIED`: required CI checks passed on the exact PR head SHA.
- `WINDOWS_VERIFIED`: owner-side Windows execution evidence recorded.
- `REAL_MEDIA_VERIFIED`: authorized real-media output was generated and validated.
- `BLOCKED`: explicit blocker recorded.
- `COMPLETE`: acceptance criteria met with evidence.

## Registry

| Chat ID | Exact chat title | Workstream ID | Scope | Branch / PR | Status | Attribution evidence |
|---|---|---|---|---|---|---|
| ARO-CHAT-0001 | Legacy chat title not reliably recoverable | ARO-GTA-LEGACY-01 | Earlier MVP / clipping foundation work; exact chat-to-PR mapping requires owner/history reconciliation | Multiple early PRs; do not infer ownership from author account | IN_PROGRESS / historical mapping unverified | Repository PR descriptions and commit history must be reconciled before assigning individual work |
| ARO-CHAT-0002 | CHAT-002 | ARO-GTA-P0-05 | FFprobe Path Propagation & Output Validation | ARO-GTA-P0-05 | Propagate selected ffprobe through direct and batch rendering; validate rendered MP4 metadata; add regression tests | `workstream/post-render-media-verification` / [PR #60](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/60) | IMPLEMENTED; tests, CI, Windows and real-media verification not established by PR evidence | PR #60 body lists Chat ID, title, workstream, commits, files and explicit unverified validation |
| ARO-CHAT-0003 | ARO-CHAT-0003 | CHAT-003 | Chat & Workstream Attribution Registry | ARO-GTA-P0-06 | Add append-only chat/workstream attribution ledger and rules | `workstream/aro-chat-registry-2026-11-20` / PR link pending | IN_PROGRESS | This registry change; exact implementation commit and PR are recorded after creation |

## New workstream entry template

Copy this row only after reserving a new unique ID:

| ARO-CHAT-NNNN | Exact owner-confirmed chat title | ARO-GTA-P0-NN | One bounded task | branch / PR URL | RESERVED | Evidence links |

## Latest audit notes

- The repository owner account may appear as the GitHub author for multiple AI-assisted PRs. Therefore GitHub's `user.login` alone does **not** identify which ChatGPT conversation performed the work.
- The reliable attribution chain is: Chat ID + Workstream ID in PR body → unique branch → commit SHAs → changed files → exact-head test/CI evidence.
- Existing historical PRs without explicit chat attribution remain `UNATTRIBUTED` until evidence is added. Do not guess.
- This registry does not rename ChatGPT conversation titles. The owner must apply the matching `ARO-CHAT-NNNN` title in the ChatGPT UI if desired.
