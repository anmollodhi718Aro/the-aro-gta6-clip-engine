# ARO-CHAT-0217 | Verify upload snapshot cleanup when the request fails

Date: 2026-11-24

## Scope
Add a regression test for the error path in the approved-byte snapshot upload lifecycle. The test uses a synthetic local file and mocked Google API modules only.

## Finding
The ARO-CHAT-0216 cleanup change closes the retained `MediaFileUpload._fd` stream in a `finally` block and attempts snapshot-directory cleanup in a nested `finally`. The existing regression covered successful PRIVATE response handling. This follow-up covers an exception raised by the mocked upload request, ensuring the stream is still closed and the snapshot path is removed.

## Change
- Add `test_upload_closes_media_stream_and_removes_snapshot_when_request_fails`.
- Use a real temporary file handle returned by a mocked `MediaFileUpload`.
- Make the mocked request raise a deterministic `RuntimeError`.
- Assert the original exception propagates, the retained stream is closed, the snapshot path no longer exists, and the API insert was attempted exactly once.
- No production code changes.

## Workstream
- Chat ID: ARO-CHAT-0217
- Exact title: ARO-CHAT-0217 | Verify Upload Snapshot Cleanup on Request Failure
- Workstream ID: ARO-GTA-P1-217
- Branch: `workstream/aro-chat-0217-upload-error-cleanup-test-2026-11-24`
- Base: `workstream/aro-chat-0216-close-upload-media-handle-2026-11-24`
- Base task: PR #328 approved-byte snapshot and ARO-CHAT-0216 media-handle cleanup follow-up
- Test commit: `707a7a882fa452bc512cc77062d0e8f0b9801c0d`

## Validation
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu and hosted-Windows CI: PENDING.
- No OAuth, credentials/tokens, real media, network upload, merge, deployment, or publishing.
- The test uses a synthetic local file and mocked API client; it does not perform an upload.

## Safety
Draft-only follow-up. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled. No merge, rebase, retarget, deployment, or destructive action.
