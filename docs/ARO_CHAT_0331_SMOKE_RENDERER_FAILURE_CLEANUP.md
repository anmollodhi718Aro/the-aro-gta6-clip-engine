# ARO-CHAT-0331 | Verify smoke cleanup after renderer failures

- Workstream: ARO-GTA-P0-331; continued the existing draft PR #386 branch and original base.
- Added regression coverage for two failure paths: the renderer raises an I/O exception after creating a partial output, and the renderer returns a non-RENDERED status.
- Both tests assert that the temporary source/output paths and their containing temporary directory are removed.
- Production code unchanged; cleanup continues to rely on the harness's `TemporaryDirectory` context manager.
- Test commit: dca3248e7f898d2082524b2dbb7bad1985d245eb.
- Unit tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/Windows CI NOT VERIFIED; independent review NOT RECORDED; authorized real MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and its original base/ancestry. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
