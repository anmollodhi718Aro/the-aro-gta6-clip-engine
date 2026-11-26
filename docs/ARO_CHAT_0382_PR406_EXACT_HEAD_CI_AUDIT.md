# ARO-CHAT-0382 | PR #406 Exact-Head CI Audit (2026-11-26)

- Workstream: ARO-GTA-P0-382.
- Parent: Draft PR #406, exact head `3899f034d803b629df65f716a6fa97eab1e1e641`.
- Preserve ancestry PR #406 -> #405 -> #404 -> #403 -> #402 -> #401 -> #400 -> #399 and all earlier dependencies.
- Branch: `workstream/aro-chat-0382-pr406-exact-head-ci-audit-2026-11-26`.
- Starting SHA: `3899f034d803b629df65f716a6fa97eab1e1e641`.

## Exact-head PR CI evidence

- PR-triggered Python CI run #45803605172 (run number 2595, event `pull_request`) explicitly references PR #406 and its exact head SHA `3899f034d803b629df65f716a6fa97eab1e1e641`; it completed FAILURE.
- Windows job #139852915564 and Ubuntu job #139852916033 both completed FAILURE.
- Job summaries expose `steps: null` and `logs_url: null`; direct step lookups returned empty arrays; log retrieval returned HTTP 404 / BlobNotFound for both jobs.
- Actions timing endpoint: `run_duration_ms: 2000`; billable WINDOWS total_ms=0 and UBUNTU total_ms=0, one job each, duration_ms=0.
- Exact-head check-run metadata reports one annotation per job; annotation contents NOT INSPECTED because the connected GitHub fetch interface rejects the annotations subresource.
- Classification: `CI_FAILURE / EXECUTION_NOT_ESTABLISHED`. No evidence checkout, compilation, or tests started. This is not an application test failure. Root cause remains UNVERIFIED.

## Separate push-event run on the same SHA

- Run #45803692099 (run number 2597, event `push`) also used the same head SHA but its metadata lists branch `workstream/aro-chat-0382-pr406-exact-head-ci-audit-2026-11-26` and contains no PR association. It is NOT the PR-triggered check for PR #406 and is not used to replace or relabel run #45803605172.
- Its Windows job #139853219207 and Ubuntu job #139853219475 also failed with no exposed steps/logs; direct step lookups were empty and logs returned 404 / BlobNotFound. Timing reports run_duration_ms=3000 and zero billable milliseconds for both jobs.
- This separate push run corroborates the pre-step failure symptom on the same commit but does not identify its root cause.

## Changes

- Documentation-only audit report, Registry, and Startup Prompt handoff.
- No production code, tests, or CI workflow changed.

## Validation and safety

- Exact PR-triggered run metadata, jobs, direct step lookups, log responses, timing, and annotation counts inspected. Separate push-event metadata and job evidence were kept distinct.
- Repository unit suite NOT RUN; hosted Ubuntu/Windows test execution NOT ESTABLISHED; synthetic FFmpeg E2E NOT VERIFIED; independent review NOT RECORDED; owner-device Windows NOT VERIFIED; authorized GTA 6 MP4 NOT PROCESSED.
- No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing.
- Stage 1 and P0 remain NOT COMPLETE. Keep PR #406 and this child OPEN / DRAFT / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
