# ARO-CHAT-0230 | Windows SQLite test cleanup regression

Date: 2026-11-25

## Workstream
- Chat ID: ARO-CHAT-0230
- Workstream ID: ARO-GTA-P1-230
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0230-windows-sqlite-test-cleanup-2026-11-25`
- Base / starting SHA: PR #361 head `3a8bc14207e9957e3920caf430935b144bfd559b`
- Parent: draft PR #361, ARO-CHAT-0228

## Failure evidence
- Parent PR #361 exact-head workflow run #45464698463 completed with Ubuntu job success and hosted-Windows job failure.
- Ubuntu job ran the unit suite and synthetic MP4/FFprobe validation successfully.
- Windows compiled successfully, then the complete unit suite reported 365 tests with one error; the synthetic render step was skipped.
- The failing test was `test_non_duplicate_integrity_error_is_not_misreported_as_duplicate`.
- Windows traceback showed `PermissionError: [WinError 32]` while `TemporaryDirectory.cleanup()` attempted to delete `rights.sqlite3`.
- The test used `with sqlite3.connect(...)`; SQLite's connection context manager manages transaction commit/rollback but does not close the connection. This left the database handle open during Windows temporary-directory cleanup.

## Change
- Imported `contextlib.closing` and wrapped the trigger-creation SQLite connection in `closing(sqlite3.connect(...))`.
- Added a short comment documenting why explicit closure is required for Windows cleanup.
- No production code, rights semantics, uploader, OAuth, media-ingestion, workflow, or publishing behavior changed.

## Validation
- The parent run is a failure and is not treated as a pass.
- Local tests in this connector session: NOT RUN.
- Follow-up exact-head Ubuntu/hosted-Windows CI: NOT YET RUN / NOT VERIFIED.
- Independent review: NOT RECORDED.
- This is a targeted portability fix hypothesis. It is not marked verified until the new exact-head run passes.

## Safety
- Draft-only continuation. No workflow retry/dispatch, merge, rebase, retarget, deployment, OAuth, credentials/tokens, real media, network upload, or publishing.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
