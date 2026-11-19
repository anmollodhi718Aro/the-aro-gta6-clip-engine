# Workstream Progress: Post-render MP4 Verification

Last updated: 2026-11-19

## Initial repository baseline

- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine` (private).
- Default branch: `main`; no changes made to it.
- Assigned base: `integration/aro-release-candidate-2026-11-19`.
- Base commit SHA: `625425987b8381c5a7d16313f5fbb96abcfcff21` (confirmed as the base SHA of active PR #55).
- Existing release integration PR #18 remains open and unmerged.
- Active related PRs checked:
  - #50: Windows launcher/smoke-test work; overlaps `batch_render.py`, `tests/test_batch_render.py`, Windows scripts and docs.
  - #54: Windows preflight; overlaps `START_CLIPPING_TODAY.bat` and `scripts/check_project.ps1`.
  - #55: subtitle pair publication; overlaps only Subtitle Studio and its tests.
- This workstream deliberately avoids those owned files. It changes the lower-level render/metadata boundary only.

## Assigned workstream

**Scope:** Verify every FFmpeg-produced temporary MP4 with ffprobe before the no-overwrite publication step. Reject malformed, duration-mismatched, dimensionless, or incorrectly sized vertical outputs without publishing them.

Status: IN PROGRESS (implementation committed; automated execution not yet available).

## Changes implemented

- `backend/app/media_probe.py`
  - Extend `MediaInfo` with optional first-video-stream width and height.
  - Ask ffprobe for codec type and frame dimensions while retaining local-file-only probing and existing duration validation.
  - Reject malformed stream lists and invalid dimension values.
- `backend/app/clipping.py`
  - Probe the temporary MP4 after FFmpeg exits and before creating the final output link.
  - Verify video metadata, duration within `max(0.5s, 5%)` of the selected range, and positive dimensions.
  - Require exact 1080x1920 dimensions for vertical output.
  - Convert post-render probe failures into a controlled `ClipRenderError`.
  - Keep temporary-file cleanup and no-overwrite publication behavior.
- `tests/test_clipping.py`
  - Add regression coverage for duration mismatch, invalid/unreadable output, and incorrect vertical dimensions.
  - Update mocked renderer tests to model successful ffprobe verification.
  - Gate the real synthetic FFmpeg test on both ffmpeg and ffprobe being installed.
- `tests/test_media_probe.py`
  - Cover video dimensions and malformed dimension metadata.
- `docs/BATCH_RENDERING.md`
  - Document the post-render validation and failure behavior.

## Validation evidence

- Source files and tests were inspected from the GitHub base branch before editing.
- Changes were committed sequentially through the GitHub contents API.
- Commit SHAs:
  - `f41f799bf68ab99f255743113f6dcf2f5e80b86b` — render verification.
  - `2d4351d98364ef10f084e0be0f42619150134604` — ffprobe dimensions.
  - `be199718e2c7990a04387997dd103816376e2442` — render regression tests.
  - `1c6977e7e9e66d60f585eb3c8a62d0c8222fe4bc` — probe tests.
  - `80cb49f4c11f102d217fe616b106a0fd7c541cce` — rendering documentation.
- Python compile/unit tests: NOT RUN in this connector-only session.
- GitHub Actions: latest observed repository runs failed before runner assignment (runner_id 0 / zero job steps); this is infrastructure failure evidence, not a code test result.
- Real Windows execution: NOT VERIFIED.
- Real owner-provided media render: NOT RUN.

## Known limitations / follow-up

- The batch CLI's optional custom `--ffprobe` path is currently used for source preflight but is not forwarded into the lower-level renderer; the new post-render verification defaults to `ffprobe` on PATH. Standard Windows setup already requires ffprobe on PATH, but custom executable-path support should be wired in a follow-up that coordinates with the active batch-render work.
- Duration tolerance is intentionally bounded at 0.5 seconds or 5% of selected duration, whichever is larger; real variable-frame-rate and unusual-container samples still need verification.
- Must run `python -m compileall -q backend tests THE_ARO_STUDIO.py` and `python -m unittest discover -s tests -v` on the exact PR head.
- On Windows, run `powershell -ExecutionPolicy Bypass -File scripts/check_project.ps1`, then use an authorized local MP4 through `START_CLIPPING_TODAY.bat`; inspect the generated MP4 with ffprobe and play it back.

## Branch / PR

- Feature branch: `fix/post-render-media-verification`.
- Base: `integration/aro-release-candidate-2026-11-19` at `625425987b8381c5a7d16313f5fbb96abcfcff21`.
- No existing PR was changed or merged. No main/shared branch was modified.
