# ARO-CHAT-0351 | Reject a Source-Aliased Synthetic Render Output

Date: 2026-11-26
Workstream: ARO-GTA-P0-351
PR: #386 (preserve OPEN / DRAFT / UNMERGED)
Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
Base: `workstream/aro-chat-0243-single-video-preflight-schema-guard-2026-11-25`
Starting observed head: `6c4992fa76f2d05bf390baef5fbe7b3e591b800a`

## Change

The synthetic single-clip smoke harness now rejects an output path that resolves to the same filesystem object as its generated source. This prevents a renderer that merely hard-links the source to the output path from satisfying the smoke harness with a matching digest while producing no distinct clip.

Added `test_smoke_harness_rejects_output_hardlinked_to_source`. The test creates only a synthetic source fixture, makes the fake renderer hard-link it to the output path, returns a matching SHA-256 and safe upload/publishing flags, and requires fail-closed rejection plus temporary-artifact cleanup.

## Commits

- Production guard: `d296c05bf5230bc4b8fec666d9767aebdf6ef545`
- Regression test: `046d28cc2ef48be515eb956b61b2c6f77a740873`

## Verification

- Source and test changes were written to the existing PR branch and read-back verification is pending.
- Unit tests: NOT RUN.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu / hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.
- No workflow dispatch/retry was performed.

## Boundaries

Keep PR #386 OPEN / DRAFT / UNMERGED on its existing base and ancestry. No merge, rebase, retarget, deployment, OAuth/credential handling, real-media processing, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Live uploads and public publishing remain disabled.
