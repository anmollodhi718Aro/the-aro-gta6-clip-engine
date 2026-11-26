# ARO-CHAT-0346 | Reject FIFO Replacement During Synthetic Output Verification

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-346
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- PR: #386 (existing draft; original branch and base preserved)
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Starting observed head: `ed93c48f129bc86b3d6e1506a5dc89972ce9c60d`

## Finding

The synthetic smoke harness hashes its rendered output through a non-following descriptor. Its implementation uses `O_NONBLOCK` where available so a pathname replaced with a FIFO between the initial `lstat()` and `open()` cannot hang the verifier. Existing tests covered symlink replacement and descriptor cleanup, but did not directly assert this FIFO race or the nonblocking open flag.

## Change

Added `test_hash_verified_output_rejects_fifo_replacement_without_blocking` to `tests/test_synthetic_single_clip_smoke.py`.

- Begin with a regular output file so the initial path inspection succeeds.
- Replace the path with a FIFO immediately before the real descriptor open.
- Require the verifier to reject the opened non-regular descriptor.
- Assert that `O_NONBLOCK` was passed to `os.open`.
- Skip only where `mkfifo` or `O_NONBLOCK` is unavailable; this is a POSIX-specific race regression.
- Use `stat.S_ISFIFO` for compatibility with the project's supported Python versions.

Production code unchanged. No media is read or rendered by this regression.

## Commits

- Initial test commit: `6d63bd53b8048d01f805c2979902da807ee1263d`
- Compatibility correction: `a707b1526c000afe8b78dfcab38b996e86579eb2`

## Verification

- Source read-back: confirmed the test method and final FIFO assertion are present.
- Unit tests: NOT RUN.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Safety and status

Keep PR #386 OPEN / DRAFT / UNMERGED and preserve its existing branch/base ancestry. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment was performed. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Live uploads and public publishing remain disabled.
