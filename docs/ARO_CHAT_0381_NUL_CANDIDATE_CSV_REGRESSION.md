# ARO-CHAT-0381 | Reject NUL Characters in Candidate CSV (2026-11-26)

- Workstream: ARO-GTA-P0-381.
- Parent: Draft PR #404 exact head `1cdb9f420d1c03ad2dee5f78ec3de35bfc277d05`.
- Branch: `workstream/aro-chat-0381-reject-nul-candidate-csv-2026-11-26`.
- Scope: reject NUL characters during streaming candidate-CSV lexical validation; add a synthetic regression for an optional field. No media, renderer, OAuth, uploader, or publishing behavior changes.

## Change
- `backend/app/single_clip_render.py`: reject U+0000 before the CSV parser consumes a line, returning the existing controlled candidate-CSV validation error.
- `tests/test_candidate_csv_nul_character.py`: verify a NUL embedded in an optional notes field is rejected.
- This prevents non-text binary content from being silently accepted as ordinary CSV metadata.

## Validation
- GitHub source write/read-back will be recorded in the PR.
- Local focused test: NOT RUN in this connector session.
- Full repository suite: NOT RUN.
- Exact-head Ubuntu/Windows CI: PENDING.
- Synthetic FFmpeg E2E: NOT RUN.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized GTA 6 MP4: NOT PROCESSED.
- Stage 1 and P0: NOT COMPLETE.

## Safety
Keep OPEN / DRAFT / UNMERGED. No workflow dispatch/retry, merge, rebase, retarget, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
