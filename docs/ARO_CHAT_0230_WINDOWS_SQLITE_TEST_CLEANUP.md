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
- Follow-up commit-associated GitHub Actions run #45465232908 completed SUCCESS on 2026-11-24. Ubuntu and hosted Windows both compiled, ran the same 365-test suite, and passed synthetic MP4/FFprobe validation. Windows skipped 4 platform-unavailable tests; Ubuntu skipped none. This is hosted CI, not owner-device verification.
- Run was associated with report commit `5709bf02a1ba57b1021520bb4678243fb94abb11`; no CI result is transferred from parent PR #361.
- Independent review: NOT RECORDED.
- This is a targeted portability fix hypothesis. It is not marked verified until the new exact-head run passes.

## Safety
- Draft-only continuation. No workflow retry/dispatch, merge, rebase, retarget, deployment, OAuth, credentials/tokens, real media, network upload, or publishing.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.

## Follow-up CI verification — 2026-11-25
- PR #362 commit-associated Actions run [#45465232908](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45465232908) completed SUCCESS.
- The workflow checked PR merge ref `6ca5d4d4572fc566ef0a7281a1e79c06a90d4297`, which merges PR head/report commit `5709bf02a1ba57b1021520bb4678243fb94abb11` into starting base `3a8bc14207e9957e3920caf430935b144bfd559b`.
- Ubuntu job `138698264359`: compilation passed; complete unittest suite ran 365 tests and returned OK; synthetic MP4/FFprobe validation passed.
- Hosted Windows job `138698263819`: compilation passed; complete unittest suite ran 365 tests and returned OK; synthetic MP4/FFprobe validation passed.
- Both jobs used the same 365-test suite; do not describe this as 730 unique tests. The synthetic render used locally generated test pattern/tone only; no GTA 6 or third-party footage. Publishing remained disabled and manual review required.
- Status: CI_VERIFIED on the PR merge ref containing the current PR head. Raw-head-only checkout was NOT demonstrated. Local tests in this connector session NOT RUN. Independent review NOT RECORDED.
- Parent PR #361's earlier Windows failure remains historical failure evidence; this follow-up run is a separate successful run for PR #362 and does not alter PR #361.
- PR #362 remains DRAFT / OPEN / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled. No workflow retry/dispatch, OAuth, credentials, real media, network upload, merge, rebase, retarget, deployment, or publishing was performed.
