# ARO-CHAT-0218 | Verify snapshot cleanup when media-handle close fails

Date: 2026-11-24

## Scope
Add a deterministic regression test for the nested-finally cleanup guarantee in the PRIVATE-only YouTube uploader. The test uses a synthetic local file, a mocked Google API client, and a mocked media handle whose close operation raises.

## Finding
The preceding cleanup implementation closes the resumable media object's retained file handle before deleting the approved-byte snapshot. Snapshot cleanup is nested in a `finally` so it is still attempted if closing the handle raises. The prior tests covered successful upload response cleanup and request-failure cleanup, but did not directly prove that cleanup is attempted when the close operation itself fails.

## Change
- Add `test_upload_attempts_snapshot_cleanup_when_media_stream_close_fails`.
- Make the mocked API return a PRIVATE response, then make the retained media handle's `close()` raise a deterministic `OSError`.
- Assert the close error remains visible, cleanup is called exactly once, the snapshot path is removed, and the API insert was attempted once.
- Production uploader behavior is unchanged.

## Workstream
- Chat ID: ARO-CHAT-0218
- Exact title: ARO-CHAT-0218 | Verify Snapshot Cleanup When Media Handle Close Fails
- Workstream ID: ARO-GTA-P1-218
- Branch: `workstream/aro-chat-0218-cleanup-after-stream-close-error-2026-11-24`
- Base: `workstream/aro-chat-0216-close-upload-media-handle-2026-11-24` (PR #333 branch)
- Scope: test-only continuation of the media-handle cleanup regression coverage.

## Validation
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu and hosted-Windows CI: PENDING.
- The test uses synthetic local bytes and mocked Google API modules only; it cannot perform a live upload.
- Owner-device Windows and real-media acceptance: NOT VERIFIED.

## Safety
Draft only. No OAuth credentials/tokens, real media, network upload, publishing, merge, rebase, retarget, deployment, or destructive action.
Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.


## CI correction — 2026-11-24
- Initial exact-head run `45428635076` failed on both Ubuntu and hosted Windows: the new test was accidentally nested under `YouTubeDestinationProfileTests`, but called `_write_upload_rights`, a helper owned by `YouTubeUploadTests`.
- Moved the test into `YouTubeUploadTests` without changing production code in commit `9bc1e8b8541a8379a67ee8424efdde246f13c8f0`.
- Follow-up exact-head CI run `45428933635` is pending; do not mark this workstream CI_VERIFIED until both platform jobs pass on the final branch head.
