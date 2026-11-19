# Workstream Progress: POSIX Render Preflight

Last updated: 2026-11-19

## Baseline

- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine` (private).
- Default branch: `main`.
- Workstream base: `integration/release-candidate`.
- Base commit: `54cefb14c23b6d5d0bf9c1c6188ee1e9092cd70a`.
- Existing integrated renderer uses local FFmpeg and ffprobe; vertical 1080x1920 output and no-overwrite publication are implemented with unit coverage.
- Existing `scripts/check_project.sh` treated FFmpeg and ffprobe as optional warnings, then printed an all-checks-passed message. That could mislead a user into believing the machine was ready for actual clipping.
- Related work checked: PR #18 is the canonical integration-to-main review; PR #48 is merged into `integration/aro-release-candidate-2026-11-19`; PR #54 owns Windows PowerShell preflight changes on a separate base; PR #55 owns subtitle pair publishing on a separate integration base. This workstream changes only the POSIX preflight script and this log.

## Assigned scope

Make the POSIX local-check script accurately enforce the runtime prerequisites for actual rendering. Do not modify Windows scripts, renderer internals, shared integration branches, or existing PRs.

## Changes

- `scripts/check_project.sh`: require Python 3.11+, FFmpeg, and ffprobe; fail immediately with installation guidance when a required executable is missing; verify both media tools can execute before compilation and unit tests.
- `docs/WORKSTREAM_PROGRESS.md`: record baseline, scope, validation state, and remaining owner-side checks.

## Validation

- Repository source and related PR diffs inspected through GitHub.
- Shell syntax check: NOT RUN in this connector session.
- Python compile and unit suite: NOT RUN in this connector session.
- FFmpeg synthetic render: NOT RUN in this connector session.
- Windows PowerShell and owner-provided media test: NOT RUN; not applicable to this POSIX-only change.
- GitHub Actions: not yet run for this branch.

## Status

- Implementation: IN PROGRESS.
- Tested: NOT STARTED.
- Verified on Windows: NOT STARTED (outside this workstream).
- Real owner media processed: NO EVIDENCE.

## Remaining

1. Run `bash -n scripts/check_project.sh`.
2. Run `bash scripts/check_project.sh` on a POSIX host with Python 3.11+, FFmpeg, and ffprobe installed.
3. Confirm missing-FFmpeg and missing-ffprobe paths exit non-zero with the expected actionable message.
4. Run the full Python suite and synthetic FFmpeg rendering test.
5. Keep the Windows owner smoke test and actual local authorized recording test as separate release gates.
