# ARO-CHAT-0382 | PR #406 Latest Exact-Head CI Audit (2026-11-26)

- Workstream: ARO-GTA-P0-382.
- Parent: Draft PR #406, exact head `3899f034d803b629df65f716a6fa97eab1e1e641`.
- Preserve ancestry PR #406 -> #405 -> #404 -> #403 -> #402 -> #401 -> #400 -> #399 and all earlier dependencies.
- Branch: `workstream/aro-chat-0382-pr406-exact-head-ci-audit-2026-11-26`.
- Starting SHA: `3899f034d803b629df65f716a6fa97eab1e1e641`.

## Exact-head CI evidence

- Commit-associated workflow lookup returned multiple runs on the same exact PR #406 head. The later run #45803692099 (run number 2595) is the latest inspected run and completed FAILURE.
- Run #45803605172 (run number 2595? prior attempt metadata; run duration 2 seconds) also failed on the same head. The latest run #45803692099 is the controlling observation for this audit.
- Latest run jobs: hosted Windows #139853219207 and Ubuntu #139853219475; both completed FAILURE.
- Job summaries expose `steps: null` and `logs_url: null`. Direct step lookups returned empty arrays. Job-log retrieval returned HTTP 404 / BlobNotFound for both jobs.
- Actions timing endpoint: `run_duration_ms: 3000`; billable WINDOWS total_ms=0 and UBUNTU total_ms=0, one job each, duration_ms=0.
- Check-run metadata for the exact head reports one annotation per job; annotation content was not retrieved through the connected GitHub fetch interface. Do not describe annotations as absent.
- Classification: `CI_FAILURE / EXECUTION_NOT_ESTABLISHED`. There is no evidence checkout, compilation, or unit tests started. This is not evidence of an application-code test failure. Root cause remains UNVERIFIED.

## Changes

- Documentation-only audit report, Registry, and Startup Prompt handoff.
- No production code, tests, or CI workflow changed.

## Validation and safety

- Exact PR #406 head, associated workflow runs, latest jobs, direct step lookups, log responses, timing, and check-run annotation counts inspected.
- Repository unit suite NOT RUN; hosted Ubuntu/Windows test execution NOT ESTABLISHED; synthetic FFmpeg E2E NOT VERIFIED; independent review NOT RECORDED; owner-device Windows NOT VERIFIED; authorized GTA 6 MP4 NOT PROCESSED.
- No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing.
- Stage 1 and P0 remain NOT COMPLETE. Keep PR #406 and this child OPEN / DRAFT / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
