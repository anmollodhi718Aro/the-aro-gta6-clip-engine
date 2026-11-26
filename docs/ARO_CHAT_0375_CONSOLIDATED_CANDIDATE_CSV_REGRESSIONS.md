# ARO-CHAT-0375 | Consolidated Candidate CSV Regression Suite

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-375
- Parent: PR #396 exact head `e205c2e74829a901f63755675f55d3bbb1502dd2`.
- Branch: `workstream/aro-chat-0375-consolidated-candidate-csv-regressions-2026-11-26`
- Scope: test-only consolidation of two existing parser regressions that were on parallel PR branches. No production code changed.

## Why this continuation exists

The latest parser work was split across parallel branches:
- PR #395 contains the duplicate-header regression but is not in PR #396's ancestry.
- PR #392 contains the escaped-quote/multiline-field regression but is not in PR #396's ancestry.
- PR #396 descends from PR #394 -> #393 -> #390 -> #389 -> #388 -> #387 -> #386.

To make one reviewable validation path without rewriting or merging existing PR history, this child branch copies the two already-reviewed test cases into the PR #396 continuation. The original PRs remain untouched.

## Added tests

- `tests/test_candidate_csv_duplicate_headers.py`: duplicate required `source_id` header names must be rejected before DictReader can overwrite the earlier field.
- `tests/test_candidate_csv_escaped_quote_multiline.py`: valid escaped quotes followed by embedded LF and CRLF within a quoted optional field remain accepted.

These tests mirror the existing regression cases in PR #395 and PR #392 respectively. They are not new production behavior.

## Validation status

- GitHub writes: PRESENT for both test files and this report.
- Local repository unit suite: NOT RUN in this connector session.
- Isolated parser harness: PASS, 6/6 focused cases using the exact `_strict_candidate_csv_lines` and `load_selected_candidate` implementations read from this branch: duplicate headers rejected; escaped quote plus embedded LF/CRLF accepted; escaped quote/comma in optional header and row accepted; valid quoted required headers accepted; malformed quote inside unquoted header rejected; trailing text after closing quote rejected. This is a source-level isolated harness, not the repository's full unit suite.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED; workflow lookup for this new head returned zero runs.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.
- Stage 1 CSV parser regression implementation: CONSOLIDATED IN THIS BRANCH; six focused source-level harness cases PASS. Full repository unit suite and exact-head CI remain OPEN.
- P0 pipeline: NOT COMPLETE.

## Safety and ancestry

Keep this PR OPEN / DRAFT / UNMERGED. Preserve PR #396 and its existing parent chain. Do not merge, rebase, retarget, or rewrite existing PRs. No workflow dispatch/retry, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.


## CI evidence correction — 2026-11-26

A later exact-head lookup returned a workflow run for the updated PR #399 head:
- Head at lookup: `8186fae808f98398ea243578ce6afe428ec56ab8`.
- Python CI run #45799569550 completed with conclusion `failure`.
- Hosted Windows job #139838950118 and Ubuntu job #139838950521 both reported `steps: null` and `logs_url: null`.
- Job-log retrieval for both returned HTTP 404 / BlobNotFound.
- Classification: `CI_FAILURE / EXECUTION_NOT_ESTABLISHED`. There is no evidence checkout, compilation, or tests started. Root cause remains UNVERIFIED and is not attributed to application code.
- No workflow dispatch or retry was initiated.

This supersedes the earlier note that the workflow lookup returned zero runs. The full repository unit suite remains NOT RUN. The 6/6 isolated source-level parser harness result remains valid but is not repository CI evidence. Ubuntu/Windows CI are NOT VERIFIED.
