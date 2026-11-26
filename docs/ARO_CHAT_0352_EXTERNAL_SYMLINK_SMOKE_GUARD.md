# ARO-CHAT-0352 | Reject External Symlink Outputs in Synthetic Smoke

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-352
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Parent PR: #386
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Base: `workstream/aro-chat-0243-single-video-preflight-schema-guard-2026-11-25`
- Starting observed PR head: `6c4992fa76f2d05bf390baef5fbe7b3e591b800a`

## Task and change

Added `test_smoke_harness_rejects_external_symlink_output_and_cleans_temporary_files` to `tests/test_synthetic_single_clip_smoke.py`.

The fake renderer points the requested output path at an unrelated file outside the smoke harness temporary directory and returns an otherwise plausible RENDERED report with a matching SHA-256. The harness must reject the symlink through the regular non-symlink output verifier. The regression verifies that external target bytes remain unchanged and the temporary source, output link, and directory are cleaned up.

Production code unchanged.

## Commits and attribution

- Test commit: `a75d9f93db64cbb9463f990930ca6cfa99b8b0b8`.
- Provisional report commit: `d01ee276d4082f90a5aa48a46e15d699286850b0`.
- Serial collision reconciliation commit: `cc58a1bc61085317188d6fcbc625c1c7fae51dda`.
- The initial ARO-CHAT-0351 attribution collided with concurrent work. This regression is uniquely assigned ARO-CHAT-0352 / ARO-GTA-P0-352. The historical alias is retained; no commit history was rewritten.

## Validation

- GitHub source read/edit/read-back only.
- Unit tests NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED.
- Independent review NOT RECORDED.
- Owner-device Windows verification NOT VERIFIED.
- Authorized real GTA 6 MP4 NOT PROCESSED.

## Safety and handoff

Keep PR #386 OPEN / DRAFT / UNMERGED on its existing branch/base. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
