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


## Exact-head Actions observation — run #45824908265 (2026-11-26)
- The run is associated with this PR head, `41e6b39c06983f69a7bcbbba39a6828b2097c73a`, and completed with conclusion `failure`.
- Windows job #139926481123 and Ubuntu job #139926481698 both completed with conclusion `failure`; the jobs response contained no recorded steps (`steps: null`) and no log URL. Direct step lookups returned empty arrays and log retrieval returned BlobNotFound in the prior inspection.
- Classification: `CI_FAILURE / EXECUTION_NOT_ESTABLISHED`. This run does not show checkout, compilation, or repository tests executing. The underlying cause remains UNVERIFIED; do not classify it as an application-code test failure or assert a runner-service root cause.
- No workflow retry or dispatch was initiated. Repository tests remain NOT RUN; synthetic FFmpeg E2E remains NOT RUN.
