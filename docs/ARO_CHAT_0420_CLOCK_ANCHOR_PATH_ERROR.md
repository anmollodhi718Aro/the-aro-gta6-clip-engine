# ARO-CHAT-0420 — Contain clock-anchor path expansion errors

Date: 2026-11-27

## Finding
`load_clock_sync()` expanded the operator-supplied JSON path with `Path.expanduser()` outside an exception boundary. Python can raise `RuntimeError` when the home directory cannot be resolved. The CLI catches `OSError`, `ValueError`, `TypeError`, and JSON decode errors, but not this raw `RuntimeError`; consequently the command could escape its controlled error contract before attempting to read the file.

## Change
- Convert only the home-directory expansion `RuntimeError` into an actionable `OSError`.
- Preserve the original exception as the cause.
- Add a regression test that injects the expansion failure and verifies the controlled exception without reading or writing files.

## Scope and validation
- Production: `backend/app/clip_pack.py`.
- Test: `tests/test_clip_pack.py`.
- No media processing, rendering, OAuth, credentials, upload, publishing, or deployment behavior changed.
- Local tests: NOT RUN.
- Exact-head CI: NOT VERIFIED.
- Synthetic FFmpeg E2E: NOT RUN.
- Independent review: NOT RECORDED.
- Authorized GTA VI media: NOT PROCESSED.

## Safety
Draft PR only; preserve parent PR #433 and all ancestry. No merge, rebase, retarget, workflow retry/dispatch, upload, publishing, or deployment. Stage 1/P0 remains INCOMPLETE.