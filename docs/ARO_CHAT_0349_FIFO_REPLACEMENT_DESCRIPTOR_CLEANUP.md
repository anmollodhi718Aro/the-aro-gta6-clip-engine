# ARO-CHAT-0349 | Close Descriptor When Synthetic Output Is Replaced by a FIFO

- Date: 2026-11-26
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Workstream: ARO-GTA-P0-349; continuation of existing draft PR #386.
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`; original PR base and ancestry preserved.
- Scope: strengthen the POSIX FIFO replacement race regression in `tests/test_synthetic_single_clip_smoke.py`.

## Change

The existing regression replaces the initially inspected regular output path with a FIFO immediately before `os.open()`. It verifies `O_NONBLOCK` is set and the verifier rejects the non-regular descriptor without blocking.

This continuation additionally captures the opened descriptor and asserts it is closed after the verifier rejects the FIFO. This directly covers the `finally` cleanup path for a post-open non-regular-file rejection.

- Test: `test_hash_verified_output_rejects_fifo_replacement_without_blocking`
- Production code unchanged.
- No media processing, OAuth, upload, publishing, or workflow dispatch.

## Validation

- Static source/read-back: committed on the existing branch.
- Local unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED; FIFO-specific regression is POSIX-gated.
- Authorized real GTA 6 MP4: NOT PROCESSED.

Preserve PR #386 OPEN / DRAFT / UNMERGED. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
