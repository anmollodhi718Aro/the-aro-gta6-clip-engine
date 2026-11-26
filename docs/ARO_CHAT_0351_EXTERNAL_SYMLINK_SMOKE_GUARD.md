# ARO-CHAT-0351 | Reject External Symlink Outputs in Synthetic Smoke

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-351
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Parent PR: #386
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Base: `workstream/aro-chat-0243-single-video-preflight-schema-guard-2026-11-25`
- Starting observed PR head before this continuation: `6c4992fa76f2d05bf390baef5fbe7b3e591b800a`

## Task

Add a focused integration regression proving that the synthetic smoke harness rejects an output path that is a symbolic link to an unrelated external file, while preserving that external file and cleaning up its temporary source/output workspace.

## Change

- Added `test_smoke_harness_rejects_external_symlink_output_and_cleans_temporary_files` to `tests/test_synthetic_single_clip_smoke.py`.
- The fake renderer creates an output symlink to a file outside the harness temporary directory and returns an otherwise plausible RENDERED report with the target's valid SHA-256.
- The harness must fail closed through its regular non-symlink output verifier.
- The regression asserts that external target bytes are unchanged and the synthetic source, output link, and temporary directory are cleaned up.
- Production code unchanged; no real media, OAuth, upload, publishing, or deployment.

## Commit

- Test commit: `a75d9f93db64cbb9463f990930ca6cfa99b8b0b8`

## Validation

- GitHub source read and edit completed.
- Unit tests NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED.
- Independent review NOT RECORDED.
- Owner-device Windows verification NOT VERIFIED.
- Authorized real GTA 6 MP4 NOT PROCESSED.

## Safety and handoff

Keep PR #386 OPEN / DRAFT / UNMERGED on its existing branch/base. Do not dispatch/retry workflows, merge, rebase, retarget, deploy, process real media, upload, or publish without separate explicit owner approval. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
