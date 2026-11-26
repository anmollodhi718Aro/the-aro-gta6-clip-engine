# ARO-CHAT-0376 | Investigate GitHub Actions Jobs Failing Before Runner Assignment

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-376
- Parent: PR #399 exact head `fea7ec2939de11841359bc7b748d9b7e609ee949`.
- Branch: `workstream/aro-chat-0376-investigate-unassigned-actions-runners-2026-11-26`
- Scope: read-only CI investigation and evidence documentation. No production code or workflow configuration changed.

## Evidence inspected

- Workflow: `.github/workflows/ci.yml`, blob `dfdd18952b338d4f76290484f0698a27e2fae1cc`.
- Workflow declares ordinary `pull_request` triggers (opened, synchronize, reopened, ready_for_review), plus push and manual dispatch.
- Workflow defines a two-OS matrix (Ubuntu and Windows) with checkout, Python 3.11 setup, FFmpeg install, compileall, unittest discovery, and synthetic clip smoke steps.
- Exact PR #399 head: `fea7ec2939de11841359bc7b748d9b7e609ee949`.
- Latest exact-head run: Python CI run #45799791858, event `pull_request`, run attempt 1, completed `failure`.
- Windows job #139839713350 and Ubuntu job #139839713764 both completed `failure` approximately two seconds after creation.
- Both job records report `steps: []`, `runner_id: 0`, blank `runner_name`, and `logs_url: null`.
- Dedicated step lookup returned empty arrays for both jobs. Job-log retrieval returned HTTP 404 / BlobNotFound for both.
- Check-run records show no title, summary, or text; each reports one annotation, but the supported GitHub connector did not expose the annotation subresource. Commit status endpoint returned zero status entries.
- The immediately preceding exact-head audit had the same pattern: run #45799693944, both OS jobs failed with empty steps and no logs. Earlier run #45799569550 also had no steps/logs.

## Assessment

- Classification: `CI_FAILURE / EXECUTION_NOT_ESTABLISHED`.
- The checked-in workflow YAML contains normal job steps and no visible condition that would skip the jobs.
- The observed records indicate that neither hosted runner was assigned and no workflow step is evidenced as having started.
- Root cause remains **UNVERIFIED**. Possible account/repository Actions policy, billing/quota, service-side scheduling, or runner provisioning causes cannot be distinguished from the available records. None is asserted as the cause.
- This is not evidence of a Python compile/test failure and must not be reported as an application-code failure.
- No workflow dispatch or retry was initiated. No workflow file was changed.

## Remaining Stage 1 gates

- Full repository unit suite: NOT RUN in a controlled local environment.
- Exact-head Ubuntu CI execution: NOT ESTABLISHED.
- Exact-head hosted-Windows CI execution: NOT ESTABLISHED.
- Synthetic FFmpeg end-to-end: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Owner-approved authorized GTA 6 MP4 processing: NOT PERFORMED.
- Stage 1: NOT COMPLETE. P0 pipeline: NOT COMPLETE.

## Next safe action

Owner/repository administrator should inspect the repository's Actions settings and account billing/usage or GitHub Actions service notices, and provide the check-run annotation details if available. After the runner-allocation cause is understood, obtain explicit owner approval before any manual workflow dispatch/retry. Do not alter CI configuration merely to mask the runner-allocation failure.

## Safety and ancestry

Keep PR #399 and this audit child OPEN / DRAFT / UNMERGED. Preserve the parent chain. No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.


## Cross-PR CI confirmation — PR #400 (2026-11-26)

- PR #400 exact head: `dcfd8f0427dbbeb59a3245d6eba78348e84e252e`; workflow run #45800768113, run number 2547, event `pull_request`, completed FAILURE within approximately three seconds.
- Windows job #139843090063 and Ubuntu job #139843090325 both completed FAILURE. Dedicated step lookups returned empty arrays; job-log retrieval for both returned HTTP 404 / BlobNotFound.
- The job-list wrapper reported `steps: null` and `logs_url: null` for both jobs. No runner/step execution is evidenced.
- This is a second consecutive PR branch (after PR #399 run #45799791858) showing the same failure-before-steps pattern. It strengthens the observation that the problem is not isolated to one PR head, but does not identify the root cause.
- Classification remains `CI_FAILURE / EXECUTION_NOT_ESTABLISHED`; root cause UNVERIFIED. Repository Actions settings and billing/service diagnostics remain unavailable through the connected read-only GitHub surface. No dispatch/retry initiated.
- PR #400's own CI is therefore also NOT VERIFIED. No code/workflow changes made. Stage 1 remains NOT COMPLETE.
