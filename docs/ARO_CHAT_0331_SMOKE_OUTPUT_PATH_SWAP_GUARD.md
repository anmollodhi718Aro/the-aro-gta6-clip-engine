# ARO-CHAT-0331 — reject synthetic output path replacement during open

- Continued the existing P0 draft PR #386 on its original branch and base.
- Static review of the synthetic output verifier identified a remaining race boundary worth locking down: the output pathname could be replaced after its initial non-following `lstat()` but before `os.open()`.
- Added a regression that swaps the candidate pathname for a symlink immediately before the verifier opens it. The verifier must reject the replacement, whether the platform enforces `O_NOFOLLOW` or the descriptor/path identity comparison detects the mismatch.
- The test also confirms the original file remains preserved and the replacement symlink is not accepted.
- Test commit: `7a7424e84f781ceb8045c44b41b1091c9b4c5df5`.
- Tests NOT RUN in this connector session. Synthetic FFmpeg end-to-end NOT RUN. Exact-head Ubuntu/Windows CI NOT VERIFIED; no workflow dispatch/retry was performed. Independent review NOT RECORDED. Authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and its existing base/ancestry. No merge, rebase, retarget, workflow dispatch/retry, real-media processing, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
