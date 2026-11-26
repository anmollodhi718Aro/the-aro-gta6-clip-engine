# ARO-CHAT-0305 — expanded report path fallback regression

- Chat ID: ARO-CHAT-0305
- Workstream ID: ARO-GTA-P1-305
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Existing PR: #386
- Existing branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`

## Finding

The terminal-report fallback fix now correctly uses the expanded report path. The previous implementation passed the raw `args.report` value to the fallback writer. A report path supplied with a home-directory shorthand could therefore reserve the expanded primary report successfully but fail to create the fallback beside it after a terminal-write failure.

## Change

- Added `test_cli_terminal_fallback_uses_expanded_report_path`.
- The regression supplies a home-relative report argument, maps its expansion to an isolated temporary directory, injects a partial terminal-report write, and verifies the fallback JSON is created beside the expanded primary report.
- The test also verifies a completed local output is preserved and the fallback retains `RENDERED` status with upload and publishing disabled.
- No production behavior changed in this workstream; it adds regression coverage for the preceding production fix.

## Validation

- Existing exact-head run #45741447981 for parent SHA `133440db0e8b29e18f89709a82b7a0d3b2621c74` failed before any job steps. Job #139647172408 had `runner_id=0`, blank runner name, and `steps=[]`; this is a runner/provisioning failure signal, not a test failure. Root cause remains UNKNOWN.
- The new regression has NOT been run locally in this connector session.
- New commit CI status must be checked from its naturally triggered run; no workflow retry or dispatch was requested.
- Independent review NOT RECORDED; owner-device Windows NOT VERIFIED; real authorized media NOT PROCESSED / NOT VERIFIED.

## Safety

- PR #386 remains OPEN / DRAFT / UNMERGED and retains its existing base and ancestry.
- No merge, rebase, retarget, workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, or deployment.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Live uploads and public publishing remain disabled.
