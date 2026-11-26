# ARO-CHAT-0320 — Durable report pathname identity guard

- Chat ID: ARO-CHAT-0320
- Workstream ID: ARO-GTA-P0-320
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Parent: existing draft PR #386; original branch and base preserved.

## Finding

The single-clip CLI keeps the report file descriptor open while it inspects media and renders. Before this change, it did not verify that the report pathname still identified the same inode. A concurrent replacement could leave terminal JSON written to an unlinked file descriptor while another file occupied the report path.

## Change

Added _report_handle_matches_path(), which compares the open descriptor's regular-file device/inode identity with a non-following lstat() of the report path. The CLI checks identity after the durable RUNNING reservation, before terminal report replacement, and after terminal report fsync.

A mismatch fails closed. The pre-media mismatch prevents renderer invocation; a terminal mismatch attempts the existing exclusive fallback report. Existing replacement files are not overwritten.

These checks narrow pathname-replacement races but do not claim a fully atomic transaction against all concurrent filesystem actors.

## Regression coverage

- test_cli_stops_before_media_when_reserved_report_path_is_replaced
- test_cli_falls_back_when_reserved_report_path_changes_during_terminal_write

## Validation and safety

- Repository tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real MP4: NOT PROCESSED.
- PR #386 remains OPEN / DRAFT / UNMERGED; original base and ancestry preserved.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
- No workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, merge, rebase, retarget, or deployment.
