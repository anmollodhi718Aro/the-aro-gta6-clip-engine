# ARO-CHAT-0357 | Verify Resolved FFmpeg and FFprobe Tool Consistency

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-357
- Parent: existing draft PR #386; original branch and base preserved.
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Scope: test-only regression for resolved executable consistency in the synthetic smoke harness.

## Change

Added `tests/test_synthetic_single_clip_smoke_tool_resolution.py`.

The regression supplies explicit FFmpeg and FFprobe paths, mocks executable lookup and fixture generation, and verifies that the resolved FFmpeg path is used for synthetic fixture generation and is forwarded unchanged to the renderer, together with the resolved FFprobe path. The mocked renderer writes only synthetic bytes; the test verifies the resulting PASS report, digest, disabled upload/publishing flags, and non-retention of temporary artifacts.

No actual FFmpeg/FFprobe process is launched, and no external or real GTA 6 footage is read. Production code unchanged.

## Commit

- Test commit: `a374c016f66139a826f3c5060b5c20413026e467`
- Test file: `tests/test_synthetic_single_clip_smoke_tool_resolution.py`

## Validation

- GitHub source write and read-back: PRESENT.
- Local unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety

Preserve PR #386 OPEN / DRAFT / UNMERGED and its original branch/base/ancestry. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
