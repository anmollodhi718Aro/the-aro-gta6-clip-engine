# ARO-CHAT-0381 | Reject NUL Characters in Candidate CSV (2026-11-26)

- Workstream: ARO-GTA-P0-381.
- Parent: Draft PR #404 exact head `1cdb9f420d1c03ad2dee5f78ec3de35bfc277d05`.
- Branch: `workstream/aro-chat-0381-reject-nul-candidate-csv-2026-11-26`.
- Scope: reject NUL characters during streaming candidate-CSV lexical validation; add a synthetic regression for an optional field. No media, renderer, OAuth, uploader, or publishing behavior changes.

## Change
- `backend/app/single_clip_render.py`: reject U+0000 before the CSV parser consumes a line, returning the existing controlled candidate-CSV validation error.
- `tests/test_candidate_csv_nul_character.py`: verify NUL rejection in an optional notes field, a header, an unselected trailing row, and a multiline quoted optional field.
- This prevents non-text binary content from being silently accepted as ordinary CSV metadata.

## Validation
- GitHub source read-back confirms the production guard and all four regression cases are present.
- Isolated source-level harness for the multiline quoted-field case rejected U+0000 as expected. This is NOT execution of the repository unittest.
- Local focused repository test: NOT RUN.
- Full repository suite: NOT RUN.
- Exact-head pull-request run #45813736851 on head `c60127c9216beebb0965323985bf304300fe4b1b` completed FAILURE after ~3 seconds. Ubuntu job #139887962075 and Windows job #139887962503 had no recorded steps; direct step lookups were empty; both job logs returned 404 / BlobNotFound. Timing: run_duration_ms=3000; billable Ubuntu and Windows total_ms=0. Classification: CI_FAILURE / EXECUTION_NOT_ESTABLISHED; root cause UNVERIFIED. This is not an application test failure.
- Synthetic FFmpeg E2E: NOT RUN.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized GTA 6 MP4: NOT PROCESSED.
- Stage 1 and P0: NOT COMPLETE.

## Safety
Keep OPEN / DRAFT / UNMERGED. No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
