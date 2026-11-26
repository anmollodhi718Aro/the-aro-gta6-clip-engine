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
- Isolated parser harness: NOT RUN yet.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED for this new head.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.
- Stage 1 CSV parser regression implementation: CONSOLIDATED IN THIS BRANCH; validation gates remain OPEN.
- P0 pipeline: NOT COMPLETE.

## Safety and ancestry

Keep this PR OPEN / DRAFT / UNMERGED. Preserve PR #396 and its existing parent chain. Do not merge, rebase, retarget, or rewrite existing PRs. No workflow dispatch/retry, deployment, OAuth, credentials, real media, upload, or publishing. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
