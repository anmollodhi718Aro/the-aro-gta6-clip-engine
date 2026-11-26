# ARO-CHAT-0308 — Terminal Fallback Regression Trigger Correction

**Date:** 2026-11-26  
**Workstream:** ARO-GTA-P1-308  
**Repository:** anmollodhi718Aro/the-aro-gta6-clip-engine  
**Existing PR:** #386  
**Branch:** workstream/aro-chat-0244-single-selected-clip-render-2026-11-25

## Finding

Static review found that `test_cli_terminal_fallback_persists_file_at_expanded_report_path` configured its `FailingWriteProxy` to inject a partial write on the third call to the primary report handle. The CLI uses that handle for two writes: the initial durable RUNNING reservation and the terminal report replacement. The third call therefore never occurs, so the test did not actually exercise terminal fallback persistence.

## Change

Changed only the final test's failure-injection condition from the third write to the second write. This targets the terminal report write after the initial RUNNING reservation and causes the intended fallback path to be exercised. Production code is unchanged.

## Commits

- Registry reservation: 2abc9a82b10a11e398c127503a0c6f596587086a
- Startup handoff: 5365fafd7003a82f7c5b26cbd56f43dd8c3c3e96
- Test-only correction: 13fc25b481b9c5d9cae95e537980df666306c3f2

## Validation

- Local tests: NOT RUN in this connector session.
- Exact-head Actions lookup for test commit: no associated workflow run returned; CI PENDING / NOT VERIFIED.
- Independent review: NOT RECORDED.
- No real media was processed.

## Safety

PR #386 remains OPEN / DRAFT / UNMERGED. Existing base and ancestry are preserved. No workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, merge, rebase, retarget, or deployment was performed. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
