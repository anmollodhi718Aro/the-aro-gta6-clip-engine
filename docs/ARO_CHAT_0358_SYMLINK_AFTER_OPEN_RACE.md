# ARO-CHAT-0358 | Reject Output Path Replacement After Descriptor Open

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-358
- Parent: existing draft PR #386; original branch and base preserved.
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Scope: focused regression test for the synthetic smoke output verifier.

## Finding

ARO-CHAT-0356 covers a symlink replacement immediately before `os.open`. A separate timing window exists after the verifier has opened a regular output file: the descriptor continues to reference the original file while the output pathname can be replaced before the verifier's final path-identity check. The verifier must reject this mismatch rather than accept a digest for a file no longer present at the requested output path.

## Change

Added `tests/test_synthetic_smoke_symlink_after_open_race.py`.

The regression captures the opened descriptor, replaces the output pathname with a symlink during the first descriptor read, and requires the verifier to fail closed during its final identity comparison. It also verifies descriptor closure and that the external target bytes remain unchanged. It uses temporary synthetic files only.

Production code unchanged. No FFmpeg/FFprobe process is launched.

## Commit

- Test commit: `d71eb490f21f83b03e9f74284e87645fe9288788`
- Test file: `tests/test_synthetic_smoke_symlink_after_open_race.py`

## Validation

- GitHub source write/read-back: PRESENT.
- Local unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety

Preserve PR #386 OPEN / DRAFT / UNMERGED and its original ancestry. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
