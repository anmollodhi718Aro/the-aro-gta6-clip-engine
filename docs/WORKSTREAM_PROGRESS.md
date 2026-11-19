# Workstream Progress: Manual Clip CLI End-to-End QA

Last updated: 2026-11-19

## Assignment

- Workstream: 01-10, manual local clipping CLI integration regression.
- Branch: `workstream/01-10-manual-clip-cli-e2e`
- Base ref: `integration/aro-release-candidate-2026-11-19`
- Base SHA: not exposed by the branch-creation response; do not infer it from the main-branch merge base.
- Scope: add isolated regression coverage for the operator's JSON → CSV → batch-render dry-run path, including Unicode and whitespace in local Windows-style paths.

## Reconnaissance

- Repository default branch: `main`.
- Main merge-base SHA reported by GitHub compare: `5f3332770b27d8a5211b3e74feade222563a9263`.
- Integration candidate is 320 commits ahead of `main`, 0 behind at reconnaissance.
- Existing open work checked:
  - PR #50 owns changes to `scripts/manual_clip_wizard.ps1`, `backend/app/batch_render.py`, and related Windows smoke coverage.
  - PR #54 owns `START_CLIPPING_TODAY.bat` and `scripts/check_project.ps1`.
  - PR #55 owns `backend/app/subtitle_studio.py` and `tests/test_subtitle_studio.py`.
- This workstream avoids all of those files.

## Implementation

- [x] Added a subprocess-level regression test for the manual clip preparation CLI followed by batch-render dry-run.
- [x] Test fixture uses a placeholder local media file; dry-run must not invoke FFmpeg or create MP4 output.
- [x] Test exercises spaces and Unicode in temporary paths.
- [ ] Run focused test.
- [ ] Run full compile and unittest suite.
- [ ] Review CI on the exact PR head.
- [ ] Windows PowerShell / real authorized media smoke test remains owner-side.

## Files changed

- `tests/test_manual_clip_cli_workflow.py` (new)

## Verification

- Test execution: NOT RUN in this connector session; GitHub repository tools can inspect and commit source but cannot execute the Python test suite in a checkout.
- FFmpeg/FFprobe render: NOT RUN.
- Windows: NOT VERIFIED.
- Real user video processed: NO.

## Status

- Implementation: IMPLEMENTED (test added).
- Focused tests: NOT STARTED.
- Full suite: NOT STARTED.
- Windows verification: NOT STARTED.
- PR: pending creation after source review.
