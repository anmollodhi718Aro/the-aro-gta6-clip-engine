# ARO-CHAT-0334 — reject synthetic output pathname replacement after open

- Continued existing P0 draft PR #386 on its original branch and base.
- Added a deterministic regression for the synthetic smoke verifier's post-open race boundary: after the verifier opens the output and begins reading through its descriptor, the test renames the original pathname and replaces it with a symlink to a different file.
- The verifier must reject the changed pathname after hashing; the test also checks that the original bytes remain at the preserved path and replacement bytes are not accepted as the output.
- Test commit: `ae2e1d432b8c023ce89186d8e1195a67bab5e3d0`.
- Tests NOT RUN in this connector session. Synthetic FFmpeg end-to-end NOT RUN. Exact-head Ubuntu/Windows CI NOT VERIFIED; no workflow dispatch/retry performed. Independent review NOT RECORDED. Authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and original base/ancestry. No workflow dispatch/retry, merge, rebase, retarget, real-media processing, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
