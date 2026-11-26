# ARO-CHAT-0384 | Reject NUL in Single-Clip Candidate CSV (2026-11-26)

- Workstream: ARO-GTA-P0-384.
- Parent: existing single-clip renderer PR #386, exact head `9291fab827d20efa0fff8005aa62e9fda9dcec3d`.
- Branch: `workstream/aro-chat-0384-reject-nul-single-clip-candidate-csv-2026-11-26`.
- Scope: reject U+0000 while streaming the complete candidate CSV before `csv.DictReader` consumes each physical line.

## Change
- Added a streaming line wrapper that raises the existing controlled CSV validation path when a NUL character is present.
- Added regressions for NUL in an optional field, a header, an unselected trailing row, and a multiline quoted field.
- The full file remains validated, so an invalid trailing row cannot hide after the selected candidate.
- No media processing, source selection, OAuth, upload, or publishing behavior changed.

## Validation
- GitHub source read-back is required after commit.
- Repository unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg E2E: NOT RUN.
- Exact-head Ubuntu/Windows CI: NOT VERIFIED; recent approved retries still fail before any recorded steps, with zero billable runner time.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety
Keep the child PR OPEN / DRAFT / UNMERGED. No merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Stage 1 remains INCOMPLETE until its actual validation and owner-side acceptance gates pass.
