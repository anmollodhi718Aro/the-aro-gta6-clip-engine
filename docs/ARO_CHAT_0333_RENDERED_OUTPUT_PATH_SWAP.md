# ARO-CHAT-0333 — reject rendered-output path replacement during hashing

- Continued the existing P0 draft PR #386 on its original branch and base.
- Added a regression around the production `_sha256_verified_regular_file` helper. It opens the rendered output, then simulates replacement of the pathname before the helper's path-stat check.
- The verifier must reject the mismatch between the opened descriptor and the current pathname. The test also confirms the original rendered bytes remain preserved at the renamed path and the replacement bytes are not mistaken for the original output.
- Test commit: `db8185aad27efd9adbad15f030206148319bcc85`.
- Test execution NOT RUN in this connector session. Synthetic FFmpeg end-to-end NOT RUN. Exact-head Ubuntu/Windows CI NOT VERIFIED. No workflow dispatch/retry.
- PR #386 remains OPEN / DRAFT / UNMERGED. No merge, rebase, retarget, media processing, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
