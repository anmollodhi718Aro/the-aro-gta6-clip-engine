# AI Chat Performance Analytics

This project keeps AI-session performance data separate from the human-readable chat/workstream registry.

## Canonical structured source

- `analytics/ai_chat_sessions.json` is the structured session ledger.
- `docs/CHAT_WORKSTREAM_REGISTRY.md` remains the identity, ownership and workstream index.
- `docs/PROJECT_HANDOFF.md` remains the canonical engineering handoff.

Do not create another competing chat registry.

## Evidence rules

- One record per participating AI conversation, keyed by unique Chat ID.
- Record provider/model as the session reports them; a provider inventory or configured name is not proof of a connected API.
- Preserve exact branch names, SHAs, commit/PR/issue links and workflow run IDs.
- Distinguish commits and files from verified deliverables.
- Record test counts only from an executed local test log or completed CI job log.
- Keep elapsed time separate from active work time. If either cannot be measured, store `null`.
- Use `null` for unknown, inaccessible, pending or unmeasured values. Do not convert missing information to zero.
- A session's final score remains `null` until it closes and its evidence is reconciled.
- Do not infer which AI conversation authored old commits from GitHub author identity alone.

## Initial ranking model

The initial configurable weights are:

| Dimension | Weight |
|---|---:|
| Task importance | 25% |
| Verified completion | 25% |
| Technical correctness | 20% |
| Test and CI evidence | 15% |
| Time efficiency | 10% |
| Documentation and handoff quality | 5% |

The raw measurements must remain visible beside any normalized score. Different task categories must be compared against their assigned scope and difficulty; file count and PR count are not quality metrics.

## Status and aggregation

Use explicit statuses such as `RESERVED`, `IN_PROGRESS`, `IMPLEMENTED`, `TESTED`, `CI_VERIFIED`, `WINDOWS_VERIFIED`, `REAL_MEDIA_VERIFIED`, `BLOCKED`, `FAILED`, and `COMPLETE`.

Dashboard aggregates must distinguish zero from unknown. For example, an empty evidence set is not proof that zero chats participated. Counts may be shown only for records actually present in the canonical ledger, with the coverage limitation visible.

## Current data coverage

The initial ledger contains the ARO-CHAT-0014 continuation record only. Historical sessions have not been backfilled because their per-chat elapsed time, active time, and some exact task attribution are not consistently evidenced. The AI leaderboard and averages should therefore remain provisional until historical records are reconciled and more sessions are recorded.

## Next implementation stages

1. Add a JSON schema and validation tests for session records.
2. Add a read-only analytics dashboard generated from the ledger.
3. Add task/provider/PR/CI evidence ingestion with explicit source provenance.
4. Add scoring and category leaderboards only after sufficient comparable records exist.


## Ledger schema and validation

- JSON Schema contract: `analytics/ai_chat_sessions.schema.json` (Draft 2020-12).
- Dependency-free runtime validator: `backend/app/analytics_validation.py`.
- The validator checks unique Chat IDs, required attribution/evidence fields, timezone-aware timestamps, timestamp ordering, finite non-negative timing values, valid PR/issue/commit identifiers, score bounds, and scoring weights summing to 1.0.
- Unknown elapsed time, active time, and scores must be explicitly represented as `null`; missing required fields and boolean/numeric impostors are rejected.
- Regression coverage: `tests/test_analytics_validation.py`; included in normal unittest discovery.


## Identity uniqueness and collision repair (2026-11-20)

- `chat_id` is a unique key across `analytics/ai_chat_sessions.json`; duplicate IDs are invalid and must fail validation.
- A historical duplicate `ARO-CHAT-0015` was found in the canonical ledger. The registry's primary assignment remains `ARO-CHAT-0015 | Windows CI Recovery and First-Clip Readiness Audit`; the separate `Exact-Head CI and Windows Verification Audit` record is re-attributed to `ARO-CHAT-0018` / `ARO-GTA-P0-18` with its original evidence preserved.
- `ARO-CHAT-0016` remains the analytics-schema validator session; `ARO-CHAT-0017` remains reserved for research; `ARO-CHAT-0019` owns the current ledger-integrity repair.
- This is a historical attribution correction, not evidence that the two prior sessions' overlapping commit references were independently authored. Preserve the recorded overlap and do not infer commit authorship from GitHub account identity.


## ARO-CHAT-0030 analytics record — 2026-11-20

- Structured session record: `analytics/ai_chat_sessions.json`.
- Chat title: `ARO-CHAT-0030 | Audio Stream Acceptance for First Clip`; provider/model: OpenAI / GPT-6.
- Workstream: ARO-GTA-P0-30; PR #71; exact implementation head `bb71afc5b4c7b9d37440d5e7e85643dd28995b7c`.
- Eight implementation commits; three regression tests added; direct local tests executed: 0.
- CI run `44700696502` passed on Ubuntu and Windows hosted runners, including compile and unit-test steps. Test count not recovered.
- Elapsed time, active time and final score remain null. Real-media and owner-device verification remain unverified.
- The implementation reservation was added after the initial code commits; this sequencing deviation is explicitly recorded.


## ARO-CHAT-0031 analytics note — 2026-11-20

- Chat: `ARO-CHAT-0031 | Test ResourceWarning Cleanup`; provider/model: OpenAI / GPT-6.
- Task: ARO-GTA-P2-31; PR #73; branch `workstream/aro-chat-0031-test-resourcewarning-2026-11-20`.
- One test-only resource hygiene fix: close the CSV reader with a context manager.
- Local tests executed: 0; PR #73 exact-head CI: NOT RUN due the workflow's `pull_request` base-branch filter targeting `main`, while PR #73 is intentionally stacked on PR #71.
- Parent PR #71 run 44700987089 passed 284 tests on each hosted platform; this is baseline evidence only, not verification of PR #73.
- No score assigned; timing and test evidence are incomplete. No merge or owner-only action.


## ARO-CHAT-0032 serial correction — 2026-11-20

- A concurrent reservation already existed as ARO-CHAT-0031 / PR #72. The duplicate draft PR #73 was closed unmerged and invalidated.
- This test-hygiene task is now attributed to ARO-CHAT-0032 / ARO-GTA-P2-32. No duplicate code was merged.
- The context-manager fix is present on the new branch; local tests and exact-head CI remain NOT VERIFIED.


### Concurrent serial collision correction

- Final inventory found both PR #72 and PR #74 using ARO-CHAT-0031 / ARO-GTA-P0-31. Owner reconciliation is required.
- This session's duplicate PR #73 was closed unmerged. Current workstream is ARO-CHAT-0032 / ARO-GTA-P2-32 in draft PR #75.


## ARO-CHAT-0033 analytics note — 2026-11-20

- Chat: `ARO-CHAT-0033 | Independent QA of PR #75 Test-Hygiene Fix`; provider/model: OpenAI / GPT-6.
- Task: ARO-GTA-P2-33; independent QA of PR #75 exact head `7d1bbd2405639b008f0c3d667caa5b8ca93c272f`.
- Actions run [44706399362](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/44706399362) completed successfully: Ubuntu job `136186999278` and Windows job `136186998767` each ran 284 tests and passed.
- Both exact-head logs were inspected. The ResourceWarning observed in the parent PR #71 run is absent on PR #75's exact head; the CSV reader now uses a context manager.
- Local tests executed by this chat: 0. Hosted CI is the test execution evidence; this chat independently inspected it.
- PR #75 remains open/draft/unmerged. No code changes, merge, deployment, upload or publishing.
- No numerical score assigned; timing and normalized quality telemetry are incomplete. Real-media and owner-device verification remain blocked/unverified.


- Documentation/analytics delivery: draft PR [#76](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/76), branch `workstream/aro-chat-0033-pr75-independent-qa-2026-11-20`, commit `87fab79327b7a7baed547c3834707cddbf9bb989`; six files changed, no code/test/workflow changes.
