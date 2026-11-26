# ARO-CHAT-0352 | Verify Explicit FFmpeg and FFprobe CLI Overrides

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-352
- Parent: existing draft PR #386; original branch/base preserved.
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Scope: focused CLI argument-forwarding regression; no production behavior change.

## Change

Added `tests/test_synthetic_single_clip_smoke_cli_args.py`.

The regression invokes the public `main()` entry point with explicit custom `--ffmpeg` and `--ffprobe` paths. It verifies that both exact values are forwarded to `run_smoke_test()`, the CLI returns exit code 0 for a controlled synthetic PASS result, and stdout remains parseable JSON matching that result.

This protects operator-supplied executable overrides from being silently ignored or replaced by defaults. The test mocks the smoke runner and does not invoke FFmpeg, FFprobe, media files, network services, or uploads.

## Commit

- Test commit: `40c96324a3bc5381527411c2dff7bf2699a21ee2`
- Changed file: `tests/test_synthetic_single_clip_smoke_cli_args.py`

## Validation

- GitHub write/read-back: commit created; source read-back pending.
- Local unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety and handoff

Preserve PR #386 OPEN / DRAFT / UNMERGED and its original branch/base/ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
