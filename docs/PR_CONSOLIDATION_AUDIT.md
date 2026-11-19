# Pull Request Consolidation Audit

**Audit owner:** ARO-CHAT-0004  
**Workstream:** ARO-GTA-P0-07  
**Audit branch:** `workstream/pr-consolidation-audit-2026-11-20`  
**Reference RC:** `feature/integrated-first-clip-launcher`  
**Audit date:** 2026-11-20

## Executive findings

This is an evidence-based triage snapshot, not approval to merge or close any PR. PR states are left unchanged.

### 1. Confirmed superseded implementation candidate: PR #32 by PR #35

- PR #32: `feat/local-authorized-video-clipping` → `main`
- PR #35: `fix/clip-render-atomic-validation` → `main`
- GitHub compare of #32 head to #35 head reports `ahead`, 5 commits ahead, 0 behind.
- #35 changes the same core files as #32 and extends them with validation hardening, usage documentation and a permission example.
- This establishes that #35's branch descends from #32's head. It is strong evidence that #32's commits are contained in #35, making #32 a superseded candidate if #35 is selected.
- Recommendation: review #35's full diff and tests, then close #32 as superseded only after confirming no unique discussion/review requirement is lost. Neither PR was merged or closed by this audit.

### 2. Shared-file overlap, not yet proven duplicate: PRs #60, #50, #21

- #60 touches `backend/app/batch_render.py` and `tests/test_batch_render.py`, plus clipping validation.
- #50 also touches those two files, along with the Windows launcher, preflight scripts, CI workflow and smoke test.
- #21 also touches those two files, adding media duration probing.
- Their bases differ: #60 targets `integration/aro-release-candidate-2026-11-19`; #50 and #21 target `integration/release-candidate`.
- Recommendation: do not merge these independently without rebasing and conflict review. Integrate the media-probe, render-validation and Windows-launcher changes in a dependency-aware sequence, then run the same tests on the resulting exact head.

### 3. Related but distinct workflow coverage: PRs #57 and #59

- #57 adds a native Windows CI workflow and modifies `tests/test_manual_clip.py`.
- #59 adds `tests/test_manual_clip_cli_workflow.py`.
- Both add `docs/WORKSTREAM_PROGRESS.md`, but their functional test scopes differ.
- Recommendation: combine documentation entries carefully; keep the Windows-native and CLI end-to-end test scopes distinct until both are verified.

### 4. Preflight overlap: PRs #58 and #54

- #58 modifies `scripts/check_project.sh` for POSIX FFmpeg preflight.
- #54 modifies `scripts/check_project.ps1` and `START_CLIPPING_TODAY.bat` for Windows preflight.
- These are platform counterparts, not duplicates. Review that they enforce consistent prerequisites and messages.

### 5. Large integration PR #18 / Option A vs Option B

- PR #18 is the broad integration candidate from `integration/release-candidate` into `main`; its changed-file list spans the Studio, ingestion, clipping, rendering, docs and tests.
- The temporary Option B branch `feature/integrated-first-clip-launcher` and Option A branch `integration/release-candidate` are diverged.
- Compare result (Option A as base, Option B as head): Option B is 1 commit ahead and 4 commits behind, with a shared merge base. The two branches are not interchangeable snapshots.
- The `.github/workflows/ci.yml` contents inspected on both branches are identical.
- Recommendation: do not retarget or merge PR #18, and do not promote Option B, until the common-base diff, test status and real-media acceptance run are reviewed.

## CI recovery evidence

- Workflow run #44542005014 for `integration/release-candidate` was retried once through GitHub's rerun-job action.
- Attempt 2 still ended in failure. Its job did not expose step details; the job-log endpoint returned 404 BlobNotFound.
- Other sampled jobs (including runs for PR #60 and the registry PR) also returned no step list and no retrievable job log.
- The workflow YAML itself contains checkout, Python 3.11 setup, compileall and unittest steps and is byte-for-byte identical on Option A and Option B.
- Therefore the available evidence does **not** identify a Python test assertion failure or a YAML difference. It indicates that GitHub did not expose a started job/step execution for the sampled runs. Exact runner/platform cause remains unproven.
- Next diagnostic: inspect repository Actions settings/usage and GitHub Actions service status from the owner account, then dispatch or rerun one controlled workflow and capture its complete run/job logs. The connected GitHub integration cannot change repository Actions settings or GitHub-hosted runner availability.

## Immediate consolidation order

1. Recover one CI run with visible job steps and logs. No mass reruns.
2. Review PR #35 as the successor candidate to #32; close #32 only after human review confirms supersession.
3. Resolve the shared `batch_render.py` / `test_batch_render.py` overlap across #60, #50 and #21 on a single integration sequence.
4. Pair #57 and #59 test coverage without discarding either scope.
5. Align #58 POSIX and #54 Windows preflight behavior.
6. Compare PR #18 / Option A against Option B from their common base.
7. Run tests on the selected exact RC head, then validate an owner-provided authorized recording and inspect the resulting MP4 with FFprobe.

## Guardrails

- No PR was merged, closed, retargeted or force-pushed during this audit.
- File overlap alone is not proof of duplicate work.
- A failed check with no job steps/logs is not evidence that tests themselves failed.
- No real-media verification is claimed.
