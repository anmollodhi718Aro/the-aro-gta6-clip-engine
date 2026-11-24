# ARO-CHAT-0218 | Restore upload media-handle cleanup on current PR #328 head

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0218
- Workstream ID: ARO-GTA-P1-218
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0218-current-head-media-cleanup-2026-11-24`
- Base / starting SHA: PR #328 current head `5ef44f391720966138b2eec1815dd223fb345dbd`
- Scope: restore cleanup of the resumable MediaFileUpload stream before deleting its approved-byte snapshot.

## Finding
- PR #333 introduced a Windows-safe cleanup sequence that closes the retained `MediaFileUpload._fd` stream before cleaning the temporary snapshot directory.
- PR #335 added a mocked request-failure regression that checks exception propagation, stream closure, and snapshot removal.
- The latest PR #328 head `5ef44f391720966138b2eec1815dd223fb345dbd` does not contain that cleanup sequence: its `finally` only calls `snapshot_dir.cleanup()`.
- PR #333 / #335 are on a stale, diverged stack relative to the latest PR #328 head. Compare of PR #335 base `1ba95524b05553665ce3428632a479abba256bcb` to PR #328 head `5ef44f391720966138b2eec1815dd223fb345dbd` reports 24 commits ahead and 9 behind, with merge base `114e5bfc4b154e0da272ed36408ab156cfdc5ab9`. No rebase or retarget was performed.

## Changes
- Initialize the media object to `None` before entering the upload try/finally.
- In a nested `finally`, close the retained `_fd` stream when present, then always attempt snapshot-directory cleanup.
- Extend the approved-snapshot/source-mutation test to assert the retained stream is closed and the snapshot is removed.
- Add a request-failure regression asserting the original request exception propagates, the retained stream closes, the snapshot path is removed, and the mocked insert is attempted once.
- No OAuth, rights, owner-approval, visibility, upload-authorization, or public-publishing behavior is changed.

## Validation
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu / hosted-Windows CI: PENDING until the new draft PR head's own run and both job logs are inspected.
- Tests use temporary local files and mocked Google API modules only. No network upload is performed.
- Owner-device Windows and real-media acceptance: NOT VERIFIED.

## Safety
- Draft-only; no merge, rebase, retarget, workflow retry/dispatch, OAuth credentials, real media, network upload, publishing, deployment, or destructive action.
- Issue #68 remains OPEN. Keep live uploads and public publishing disabled pending independent security review and owner-controlled acceptance.


## Close-failure regression follow-up — 2026-11-24
- Added `test_upload_removes_snapshot_when_media_stream_close_raises` on the current PR #339 branch.
- The mocked stream closes its underlying file and then raises `OSError`. The test asserts the close error propagates, the stream is closed, the approved-byte snapshot is removed by the nested `finally`, and the YouTube insert is attempted exactly once.
- Test commit: `a07cf1d0e1023f6291cf69bb6998c4f43c972fdf`.
- Local tests NOT RUN in this connector session. Exact-head Ubuntu/hosted-Windows CI must be inspected for the final branch head; owner-device Windows and real-media PRIVATE acceptance remain NOT VERIFIED.
- No OAuth, real media, network upload, merge, deployment, or publishing. Issue #68 remains OPEN; keep live uploads/public publishing disabled.


## Exact-once close assertion — 2026-11-24
- Follow-up test commit: `cc4dca770655a7bd69d767f9cb164d133e00eafd`.
- The close-failure mock now counts calls and asserts the retained stream's close is attempted exactly once, while the nested cleanup still removes the snapshot and the mocked insert occurs once.
- PR #339 latest code/test head is recorded separately in GitHub metadata. Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED (no associated run/status returned for this head). Local tests NOT RUN. Independent review NOT RECORDED.
- No OAuth, real media, live upload, merge, deployment, or publishing. Issue #68 remains OPEN; keep live uploads/public publishing disabled.


## PRIVATE-only visibility hardening — 2026-11-24
- Code commit: `e21f377583df944f5489e7d6a359bb5d2d1e6438`.
- Test commit: `598c9c488c34143c6cb8c0a9d86208e3e7ef74b1`.
- The upload metadata builder now rejects `unlisted` and `public`; CLI `--privacy` accepts only `private`. Added regression coverage proving both non-private values are rejected by metadata construction and upload validation.
- Docs commit: `51dbcdf38c59c6f74d239014fbb92019b6d50201`; corrected `docs/YOUTUBE_UPLOAD.md` to state that public publishing is not implemented and only PRIVATE staging is supported.
- CI run #45433283842 was cancelled during FFmpeg/FFprobe setup on both Ubuntu and Windows; it did not reach compile/tests. A later run #45433336438 is pending for the documentation head. Exact-head green CI is NOT VERIFIED.
- PR #339 is OPEN/DRAFT/UNMERGED and mergeable at last metadata check. Parent PR #328 is reported non-mergeable against its base; do not merge or retarget without a dependency-graph review. Independent security review NOT RECORDED. Issue #68 remains OPEN.
- No OAuth, credentials, real media, network upload, merge, deployment, or publishing.


## CI assertion correction — 2026-11-24
- First private-only hardening CI run #45433336438 exposed one stale test expectation: the test still expected the generic word `privacy`, while the stricter code now emits the intentional PRIVATE-only policy error. The implementation behavior was correct; 350 tests passed and one assertion failed on Ubuntu. Hosted Windows was cancelled before test execution.
- Updated the test assertion to expect the PRIVATE-only policy message in commit `52c168d4a389ab7a99bff5f660708382d00079df`.
- Follow-up CI run #45433572590 is now running on that exact head; both Ubuntu and hosted Windows jobs are in progress. Do not mark CI green until both complete.


## Exact-head CI closeout and scoped review — 2026-11-24

- PR #339 head: `b0a5e3e1adcff9f7a2f3715b6ba7a0c138a50722`.
- Commit-associated Actions run: [45433728254](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45433728254), completed SUCCESS.
- Both jobs checked out merge ref `5f5bf9f`, merging the audited PR head into base `5ef44f391720966138b2eec1815dd223fb345dbd`. Raw-head-only checkout is NOT DEMONSTRATED.
- Ubuntu job `138585890652`: compile passed; 351 tests passed; synthetic MP4/FFprobe step passed.
- Hosted-Windows job `138585891624`: compile passed; the same 351-test suite ran, 3 FIFO-only tests skipped because `os.mkfifo` is unavailable; synthetic MP4/FFprobe step passed.
- Both jobs ran the same 351 tests, not 702 unique tests. Synthetic logs identify locally generated test pattern/tone; `upload_performed=false`, `publishing_enabled=false`, and `manual_review_required=true`.
- This is hosted CI evidence only. Owner-device Windows, real-media acceptance, OAuth, a YouTube network upload, and independent security review remain NOT VERIFIED / NOT RECORDED.

### Scoped code-review pass of this PR's own delta

- Reviewed the uploader change and associated tests for media-handle cleanup and visibility restrictions.
- Cleanup initializes the media handle before the guarded upload block, attempts the retained media stream close before snapshot cleanup, and nests snapshot cleanup so it is attempted even if close raises.
- Tests cover close-on-success, request-failure cleanup, close-error propagation with exactly one close attempt, snapshot removal, and exactly one mocked insert.
- PRIVATE-only metadata validation and CLI choices reject UNLISTED/PUBLIC; regression tests exercise both values.
- No defect was identified in this bounded PR #339 delta. This is a scoped assistant review, NOT an independent reviewer approval of the inherited uploader/approval security lineage.
- PR #339 review submissions and inline review threads remain empty. Full independent review of the consolidated uploader/approval implementation is still required.

### Current disposition

- PR #339 remains OPEN / DRAFT / UNMERGED. Parent PR #328 has a separate non-mergeable ancestry concern; do not merge, rebase, or retarget automatically.
- Issue #68 remains OPEN and assigned to the repository owner; assignment is not approval to enable live uploads.
- Keep live uploads and public publishing disabled. No OAuth credentials, real media, network upload, merge, deployment, or publishing were used in this audit.


### Documentation follow-up head distinction

- The green run above validates the functional PR head `b0a5e3e1adcff9f7a2f3715b6ba7a0c138a50722` via its merge-ref checkout.
- Subsequent commits in this work session update only the three documentation files (workstream report, startup handoff, and registry). The latest documentation-only branch tip has no associated Actions run returned; therefore latest-tip CI is NOT VERIFIED.
- No application code or tests changed after the green functional head. Do not describe the current documentation-only tip as independently CI-verified.


## Current branch-tip CI verification — 2026-11-24

- Current PR #339 head: `a08a69cfa687479c58ce72a322b1357761a92723`.
- Commit-associated Actions run: [45434843065](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45434843065), completed SUCCESS.
- Ubuntu job `138589783324`: compile passed; 351 tests passed; synthetic MP4/FFprobe passed.
- Hosted-Windows job `138589782758`: compile passed; same 351-test suite passed; 3 FIFO-only tests are unavailable/skipped on this runner because `os.mkfifo` is not provided; synthetic MP4/FFprobe passed.
- Both platforms ran the same 351-test suite, not 702 unique tests. The run logs identify generated synthetic pattern/tone only; `gta6_footage_used=false`, `third_party_media_used=false`, `upload_performed=false`, `publishing_enabled=false`, and `manual_review_required=true`.
- This closes the earlier documentation's "current documentation-only tip CI pending" status for the exact current branch tip. The run is associated with the PR head, but hosted CI does not establish owner-device Windows acceptance or real-media behavior. OAuth, network upload, and public publishing were not exercised.
- PR #339 remains OPEN / DRAFT / UNMERGED. Issue #68 remains OPEN. Independent security review of the full consolidated uploader/approval lineage is NOT RECORDED. Parent PR #328 remains non-mergeable against its base; dependency ancestry reconciliation remains required.
- Next authorized task: review the full uploader/approval lineage independently and map the PR #311 → #328 → #339 dependency graph using exact commit ancestry. Do not merge, rebase, retarget, access OAuth credentials, upload real media, deploy, or publish. Keep all live/public upload gates disabled.
