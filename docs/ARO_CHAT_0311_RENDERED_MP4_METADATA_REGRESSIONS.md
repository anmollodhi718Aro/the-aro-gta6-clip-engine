# ARO-CHAT-0311 — rendered MP4 metadata regression coverage

Date: 2026-11-26

## Scope

Continue the existing single-selected-clip pipeline on PR #386. The production gate introduced in the preceding workstream requires a rendered result to report:
- an MP4-compatible FFprobe container name;
- at least one video stream;
- H.264 as the first mapped video stream codec; and
- positive integer width and height, excluding booleans.

This continuation adds direct regression coverage for the helper's acceptance and rejection cases. It does not change production behavior.

## Tests added

- `test_rendered_mp4_validation_accepts_h264_video_with_dimensions`
- `test_rendered_mp4_validation_rejects_missing_video_stream`
- `test_rendered_mp4_validation_rejects_missing_or_boolean_dimensions`

The dimension regression covers a missing width, a boolean height, and a zero width. The earlier integration regressions continue to cover a non-MP4 container and non-H.264 video codec.

## Commit

- Test commit: `d4a2e8482dc2d4623bd0c65e5cbbeba6b8c41ac2`

## Verification state

- Static source review: completed for this change.
- Python tests: NOT RUN in this connector session.
- Exact-head GitHub Actions: NOT VERIFIED; no run/status was returned for the inspected head.
- Independent review: NOT RECORDED.
- Authorized GTA 6 MP4: NOT PROCESSED.
- Owner playback review: NOT DONE.
- Upload/publishing/deployment: NOT PERFORMED.

## Guardrails

Continue on existing PR #386 and its existing branch/base. Preserve OPEN / DRAFT / UNMERGED state and ancestry. No workflow dispatch/retry, merge, rebase, retarget, OAuth/credential work, real-media processing, upload, publishing, or deployment was performed. Issue #68 remains deferred as WAITING_FOR_OWNER_APPROVAL.
