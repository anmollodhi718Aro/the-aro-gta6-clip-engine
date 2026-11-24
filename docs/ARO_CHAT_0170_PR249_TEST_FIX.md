# ARO-CHAT-0170 | PR #249 CLI upload-limit test fixture repair

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0170
- Exact title: ARO-CHAT-0170 | PR #249 CLI Upload-Limit Test Fixture Repair
- Workstream ID: ARO-GTA-P1-170
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0170-pr249-cli-upload-limit-test-fix-2026-11-24`
- Base / starting SHA: PR #249 head `75854f6cbead27c42d723a72f883eb7f804665f9`
- Parent PR: #249
- Scope: narrow test-fixture repair only; no production uploader behavior changes.

## Duplicate-work check
- No open PR or registry reservation for ARO-CHAT-0170 was found before branch creation.
- This follow-up is based on PR #249's exact head and does not alter PR #249 or its branch.

## Evidence and diagnosis
- PR #249 exact-head commit `75854f6cbead27c42d723a72f883eb7f804665f9` is associated with Python CI run #45314464029 (run 1135).
- Ubuntu job #138177936952: setup, checkout, Python setup, FFmpeg/FFprobe installation, and compile passed; 340 tests ran with one failure; synthetic MP4/FFprobe step skipped.
- Hosted-Windows job #138177937472: setup, checkout, Python setup, FFmpeg/FFprobe installation, and compile passed; the same 340-test suite ran with one failure; synthetic MP4/FFprobe step skipped.
- Both platforms failed `test_cli_passes_exact_clip_and_source_to_upload_boundary`. The CLI fixture supplied `--upload` but omitted the newly mandatory `--max-upload-bytes` option. The CLI correctly failed closed before calling the mocked upload boundary.
- This is a stale test invocation, not evidence of a production uploader defect. The fix supplies `DEFAULT_MAX_UPLOAD_BYTES` explicitly and asserts the exact value reaches the mocked upload boundary.

## Changes
- `tests/test_youtube_upload.py`: add explicit `--max-upload-bytes` to the live-upload CLI fixture and assert forwarding.
- `docs/ARO_CHAT_0170_PR249_TEST_FIX.md`: record exact-head CI evidence and repair scope.
- `docs/CHAT_WORKSTREAM_REGISTRY.md`: register this bounded follow-up.
- Production code, workflow files, secrets, OAuth, and publishing behavior remain unchanged.

## Validation
- Local tests: NOT RUN in this connector session.
- Follow-up branch exact-head CI: PENDING until GitHub Actions runs on the resulting PR head.
- Do not transfer PR #249's failing CI to this repair branch, and do not claim TESTED or CI_VERIFIED before its own logs are inspected.

## Safety
- No credentials/tokens, OAuth, real media, network upload, public publishing, workflow retry, merge, rebase, retarget, deployment, or destructive action.
- No live upload is enabled by this change. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; keep live/public uploads disabled pending independent security review and owner-controlled integration.
