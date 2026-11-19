# Workstream Progress: POSIX Render Preflight

Last updated: 2026-11-19

## Baseline

- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine` (private).
- Default branch: `main`.
- Workstream base: `integration/release-candidate` at `54cefb14c23b6d5d0bf9c1c6188ee1e9092cd70a`.
- Existing integrated renderer uses local FFmpeg and ffprobe; vertical 1080x1920 output and no-overwrite publication are implemented with unit coverage.
- Existing `scripts/check_project.sh` treated FFmpeg and ffprobe as optional warnings, then printed an all-checks-passed message. That could mislead a user into believing the machine was ready for actual clipping.
- Related work checked: PR #18 is the canonical integration-to-main review; PR #48 is merged into `integration/aro-release-candidate-2026-11-19`; PR #54 owns Windows PowerShell preflight changes on a separate base; PR #55 owns subtitle pair publishing on a separate integration base.

## Assigned scope

Make the POSIX local-check script accurately enforce the runtime prerequisites for actual rendering. Avoid Windows scripts, renderer internals, shared integration branches, and existing PRs.

## Changes implemented

- `scripts/check_project.sh`: require Python 3.11+, FFmpeg, and ffprobe; fail with actionable installation/PATH guidance when a required executable is missing; execute both media tools' version checks before compilation and unit tests.
- `docs/WORKSTREAM_PROGRESS.md`: record baseline, scope, validation state, and remaining owner-side checks.
- Feature branch: `workstream/posix-render-preflight`.
- Script commit: `10f166224e449b544296a920ff70d27fe19097fc`.
- Work-log commit: `2295a78fac2fb7b15dc0023449cf4beae3205639`.
- Pull request: [#58](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/58), Draft, targeting `integration/release-candidate`.

## Validation evidence

- Inspected the exact PR diff and fetched both changed files back from the feature branch.
- GitHub Actions workflow runs for head `2295a78fac2fb7b15dc0023449cf4beae3205639`: none returned at the time of inspection.
- Combined commit status: no statuses returned.
- `bash -n scripts/check_project.sh`: NOT RUN in this connector session.
- Python compile and unit suite: NOT RUN in this connector session.
- FFmpeg synthetic render: NOT RUN in this connector session.
- Windows PowerShell and owner-provided media test: NOT RUN; outside this POSIX-only workstream.

## Status

- Implementation: IMPLEMENTED.
- Tested: NOT STARTED.
- Verified on Windows: NOT STARTED (separate release gate).
- Real owner media processed: NO EVIDENCE.
- PR: OPEN, DRAFT, NOT MERGED.

## Remaining

1. Run `bash -n scripts/check_project.sh`.
2. Run `bash scripts/check_project.sh` on a POSIX host with Python 3.11+, FFmpeg, and ffprobe installed.
3. Confirm missing-FFmpeg and missing-ffprobe paths exit non-zero with the expected actionable message.
4. Run the full Python suite and synthetic FFmpeg rendering test.
5. Complete the separate Windows owner smoke test and real authorized-recording test before calling the product verified.
