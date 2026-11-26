# ARO-CHAT-0356 | Reject Symlink Replacement at Synthetic Output Open

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-356
- Parent: existing draft PR #386; original branch and base preserved.
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Scope: add a focused regression for a symlink swapped into the synthetic smoke output path after its initial `lstat()` and immediately before `os.open()`.

## Regression

- Added `tests/test_synthetic_smoke_symlink_open_race.py`.
- The test starts with a regular output file, swaps the path to a symlink immediately before the real open, and disables `O_NOFOLLOW` for this test so the portable descriptor/path identity comparison is exercised.
- It requires fail-closed rejection when the opened descriptor no longer matches the initial path identity.
- It verifies the opened descriptor is closed and the external target bytes remain unchanged.
- Uses temporary synthetic files only; no real GTA 6 media, network access, upload, or publishing.

## Commit

- Regression test commit: `6653b9980e733cff11c264e83655ec22ee441347`

## Validation

- GitHub source write: committed.
- Source read-back: pending.
- Local unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety and handoff

Keep PR #386 OPEN / DRAFT / UNMERGED on its original ancestry. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
