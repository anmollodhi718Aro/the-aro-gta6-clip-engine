# ARO-CHAT-0306 — end-to-end expanded report-path fallback regression

- Chat ID: ARO-CHAT-0306
- Workstream ID: ARO-GTA-P1-306
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Existing PR: #386
- Existing branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`

## Scope and relationship to ARO-CHAT-0305

ARO-CHAT-0305 owns the production fix that passes the expanded report path to the terminal fallback helper, plus a direct assertion that the helper receives that expanded path. This continuation adds complementary end-to-end regression coverage: it forces a partial terminal report write and verifies that a parseable fallback file is actually created beside the expanded primary report, while preserving the completed output.

## Change

- Added `test_cli_terminal_fallback_persists_file_at_expanded_report_path`.
- The test supplies a home-relative report argument, maps expansion into an isolated temporary directory, injects a partial terminal-report write, and verifies the fallback JSON is persisted beside the expanded report.
- The test also verifies the completed output bytes remain intact and the fallback records `RENDERED` with upload and publishing disabled.
- No production behavior changed in this continuation.

## Commits

- Regression test: `044f313f83d368d188444e6a5915e64e8be73a09`
- Initial report: `c4c673578d1ba265a620773712ceeda2d3f14574`
- Registry and startup attribution corrections are recorded in subsequent branch history.

## Validation

- Parent exact-head run #45741447981 failed before visible job steps: job #139647172408 had `runner_id=0`, blank runner name, and `steps=[]`. This is not evidence of a Python test failure; root cause remains UNKNOWN.
- Subsequent naturally triggered runs on later branch commits also failed before steps with the same runner metadata pattern.
- This supplemental regression was NOT RUN locally in this connector session. CI for the latest branch head is NOT VERIFIED; independent review NOT RECORDED.
- Owner-device Windows verification and authorized real-media acceptance remain NOT VERIFIED.

## Safety

- Existing PR #386 remains OPEN / DRAFT / UNMERGED with its original base and ancestry.
- No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
