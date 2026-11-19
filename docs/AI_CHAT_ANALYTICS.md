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
