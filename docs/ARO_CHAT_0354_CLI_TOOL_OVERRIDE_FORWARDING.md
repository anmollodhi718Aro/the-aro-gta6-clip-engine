

> **Serial-collision correction (2026-11-26):** This file is a historical alias only. The CLI override regression in test commit `40c96324a3bc5381527411c2dff7bf2699a21ee2` was already canonically assigned to ARO-CHAT-0352 / ARO-GTA-P0-352, with canonical report commit `47a06e8749f71743429c048fefdfa0e300e42325`. ARO-CHAT-0354 is not assigned to this test; the duplicate attribution in this filename is superseded. No commit history was rewritten.

# ARO-CHAT-0354 | Verify Synthetic Smoke CLI Tool Override Forwarding

- Date: 2026-11-26
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Workstream: ARO-GTA-P0-354; continuation of existing draft PR #386.
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`; original PR base and ancestry preserved.

## Change

Added `tests/test_synthetic_single_clip_smoke_cli_args.py` in commit `40c96324a3bc5381527411c2dff7bf2699a21ee2`.

The regression invokes the public `main()` entry point with explicit `--ffmpeg` and `--ffprobe` overrides. It verifies that both values are forwarded unchanged to `run_smoke_test()`, the CLI returns success for a controlled synthetic PASS payload, and stdout remains parseable JSON. This test does not execute FFmpeg/FFprobe or process media.

## Validation

- Static commit/diff review and source read-back: completed.
- Unit tests: NOT RUN.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head CI: NOT VERIFIED; latest lookup returned no workflow runs and no combined status checks.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Owner approval boundaries

Keep PR #386 OPEN / DRAFT / UNMERGED. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
