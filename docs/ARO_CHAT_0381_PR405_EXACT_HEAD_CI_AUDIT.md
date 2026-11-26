# ARO-CHAT-0381 | PR #405 Exact-Head CI Execution Audit (2026-11-26)

- Workstream: ARO-GTA-P0-381.
- Parent: Draft PR #405 exact head `c53bbc52989aea0c05def7051b9b0c465297d246`; preserve PR #405 -> #404 -> #403 -> #402 -> #401 -> #400 -> #399.
- Branch: `workstream/aro-chat-0381-pr405-exact-head-ci-failure-audit-2026-11-26`.
- Starting SHA: `c53bbc52989aea0c05def7051b9b0c465297d246`.

## Exact-head run

- Python CI run #45803428937 (run number 2580) is associated with the exact PR #405 head `c53bbc52989aea0c05def7051b9b0c465297d246`; completed FAILURE.
- Windows job #139852311547 and Ubuntu job #139852311065 both completed FAILURE.
- Job summaries report `steps: null` and `logs_url: null`; direct step lookups returned empty arrays; job-log retrieval returned HTTP 404 / BlobNotFound.
- Actions timing endpoint: `run_duration_ms=4000`; billable WINDOWS and UBUNTU `total_ms=0`, one job each, `duration_ms=0`.
- Classification: `CI_FAILURE / EXECUTION_NOT_ESTABLISHED`. The exact-head CI did not provide evidence that checkout, compilation, or tests started. Do not label it an application test failure.
- Root cause remains UNVERIFIED. The prior push-event run #45803137718 remains separately classified as NOT exact-head for PR #403 due to its head-SHA/base-SHA mismatch.

## Changes

- Documentation-only exact-head audit. No production code, tests, or workflow YAML changed.
- Updated this report, the workstream Registry, and the Startup Prompt handoff.

## Validation and safety

- Exact PR head and run association checked; job summaries, direct steps, logs, and timing endpoint inspected.
- Repository unit suite NOT RUN; hosted Ubuntu/Windows test execution NOT ESTABLISHED; synthetic FFmpeg E2E NOT VERIFIED; independent review NOT RECORDED; owner-device Windows NOT VERIFIED; authorized GTA 6 MP4 NOT PROCESSED.
- No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing.
- Stage 1 and P0 remain NOT COMPLETE. Keep OPEN / DRAFT / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
