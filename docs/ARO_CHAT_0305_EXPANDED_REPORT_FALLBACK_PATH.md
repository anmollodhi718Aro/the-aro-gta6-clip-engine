# ARO-CHAT-0305 — expanded report-path terminal fallback

## Finding
The single-clip CLI expands the operator's `--report` path with `expanduser()` before reserving the report. On terminal-report write failure, however, the fallback helper was passed the original unexpanded `args.report`. With a report path beginning with `~`, fallback creation could therefore target a different literal path rather than the directory containing the reserved report.

## Change
- Pass the already-expanded `report_path` to `_write_exclusive_terminal_fallback()`.
- Add a CLI regression that supplies a tilde-prefixed report path, forces a short terminal write, and asserts the fallback helper receives the expanded path.
- No media processing, OAuth, upload, publishing, or workflow configuration changes.

## Attribution
- Chat ID: ARO-CHAT-0305
- Workstream: ARO-GTA-P1-305
- Existing branch / PR: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25` / Draft PR #386
- Production commit: `133440db0e8b29e18f89709a82b7a0d3b2621c74`
- Regression test commit: `95da4200a4d94d84d6a23dd4278d76e4d48b439e`

## Validation and safety
- Repository tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: no associated runs or combined status entries were returned for test commit `95da4200a4d94d84d6a23dd4278d76e4d48b439e`; CI PENDING / NOT VERIFIED.
- Independent review: NOT RECORDED.
- PR #386 remains draft/open/unmerged. Its existing ancestry is preserved.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Live uploads and public publishing remain disabled.
- No workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, merge, rebase, retarget, or deployment was performed.
