# ARO-CHAT-0217 | Verify upload snapshot cleanup when the request fails

Date: 2026-11-24

## Scope
Add a regression test for the error path in the approved-byte snapshot upload lifecycle. The test uses a synthetic local file and mocked Google API modules only.

## Finding
The ARO-CHAT-0216 cleanup change closes the retained MediaFileUpload._fd stream in a finally block and attempts snapshot-directory cleanup in a nested finally. The existing regression covered successful PRIVATE response handling. This follow-up covers an exception raised by the mocked upload request, ensuring the stream is still closed and the snapshot path is removed.

## Change
- Add test_upload_closes_media_stream_and_removes_snapshot_when_request_fails.
- Use a real temporary file handle returned by a mocked MediaFileUpload.
- Make the mocked request raise a deterministic RuntimeError.
- Assert the original exception propagates, the retained stream is closed, the snapshot path no longer exists, and the API insert was attempted exactly once.
- No production code changes.

## Workstream
- Chat ID: ARO-CHAT-0217
- Exact title: ARO-CHAT-0217 | Verify Upload Snapshot Cleanup on Request Failure
- Workstream ID: ARO-GTA-P1-217
- Branch: workstream/aro-chat-0217-upload-error-cleanup-test-2026-11-24
- Base at branch creation: workstream/aro-chat-0216-close-upload-media-handle-2026-11-24 at PR #328 head 114e5bfc4b154e0da272ed36408ab156cfdc5ab9
- Test commit: 707a7a882fa452bc512cc77062d0e8f0b9801c0d
- Audited PR: #335; current head: 2779aee7b752433b72753ea77419f8ce3d1ae806

## Exact-head CI evidence
- Commit-associated Python CI run #45428127882 (run 1382) completed SUCCESS for the current PR #335 head.
- Ubuntu job #138565727306 and hosted-Windows job #138565727802 both completed checkout, Python setup, FFmpeg/FFprobe installation, compile, full unittest suite, and synthetic MP4/FFprobe steps successfully.
- Both jobs checked out PR merge ref refs/remotes/pull/335/merge at merge SHA 11f6105, merging PR #335 head 2779aee7b752433b72753ea77419f8ce3d1ae806 into base 1ba95524b05553665ce3428632a479abba256bcb. Raw-head-only checkout is NOT DEMONSTRATED.
- Ubuntu: 342 tests in 5.277s; OK. Hosted Windows: the same 342 tests in 11.214s; OK. These are 342 shared test cases executed on two platforms, not 684 unique tests.
- The new test test_upload_closes_media_stream_and_removes_snapshot_when_request_fails passed on both platforms.
- Synthetic render reports identify locally generated pattern/tone only: gta6_footage_used=false, third_party_media_used=false, publishing_enabled=false, manual_review_required=true. The mocked approval fixture reports upload_performed=false. No real upload occurred.
- Combined legacy commit status for the source head returned zero status entries; the two completed workflow jobs provide the observed CI result.
- PR #335 review submissions and inline review threads returned empty arrays; independent review NOT RECORDED.
- Local tests NOT RUN in this connector session. Hosted-Windows CI is not owner-device Windows verification; synthetic media is not GTA 6 footage or real-media acceptance.

## Branch ancestry note
The base branch advanced after this branch was created. Current comparison against workstream/aro-chat-0216-close-upload-media-handle-2026-11-24 reports 4 commits ahead and 4 behind, with merge base d402b913385d2772b545cae281dc5411c487d016. CI ran on merge base SHA 1ba95524b05553665ce3428632a479abba256bcb. Preserve the branch as draft; no automatic rebase or retarget was performed.

## Status
- Regression: IMPLEMENTED.
- PR #335 CI: CI_VERIFIED on its GitHub merge ref only.
- Independent review: NOT RECORDED.
- Owner-device Windows: NOT VERIFIED.
- Real-media acceptance: NOT VERIFIED.
- PR remains draft/open/unmerged; no merge requested.

## Safety
Draft only. No OAuth credentials/tokens, real media, network upload, publishing, workflow retry, merge, rebase, retarget, deployment, or destructive action.
Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
