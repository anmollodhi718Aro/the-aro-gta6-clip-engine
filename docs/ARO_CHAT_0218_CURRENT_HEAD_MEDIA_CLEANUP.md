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
