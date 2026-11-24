# ARO-CHAT-0213 | CI for every pull-request base

Date: 2026-11-24

## Finding

The default-branch workflow at the time of this change used:

```yaml
pull_request:
  branches: [main]
```

That filter excludes stacked pull requests whose base is another feature or integration branch. The active approval-record hardening chain uses feature-branch bases, so its PR-triggered workflow lookup returned no runs. A workflow_dispatch capability on a feature branch does not itself make the default-branch pull_request trigger match those PRs.

## Change

- Remove the pull_request base-branch filter so PRs targeting main and stacked feature branches are eligible.
- Retain the opened, synchronize, reopened and ready_for_review event types.
- Add manual workflow_dispatch support.
- Add concurrency cancellation scoped to the PR number or ref.
- Run the same compile and unittest commands on hosted Ubuntu and hosted Windows.
- Keep the workflow read-only with contents: read.

## Scope and safety

This change only configures CI. It does not run or retry a workflow, modify uploader behavior, access OAuth credentials, process media, upload, publish, merge, rebase, retarget or deploy.

## Validation limits

The pull request is proposed against main so the current main workflow can run its existing Ubuntu job for this change. The new Windows job and broadened trigger become active only after this workflow change is separately reviewed and merged. No CI result is claimed in this report.
