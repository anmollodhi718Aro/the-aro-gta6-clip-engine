# ARO-CHAT-0332 | Verify synthetic fixture timeout cleanup

- Workstream: ARO-GTA-P0-332; continued the existing draft PR #386 and original branch/base.
- Added a regression for FFmpeg synthetic-fixture generation timing out at the configured 120-second limit.
- The test verifies the timeout propagates as a failure, the renderer is never called, and the temporary source path and containing temporary directory are removed.
- Production code unchanged; the existing TemporaryDirectory context manager owns cleanup.
- Test commit: f4f3eb625c36051f1c014ecca10f90dcdbc376c4.
- Unit tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/Windows CI NOT VERIFIED; independent review NOT RECORDED; authorized real MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and its original base/ancestry. No workflow dispatch/retry, merge, rebase, retarget, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
