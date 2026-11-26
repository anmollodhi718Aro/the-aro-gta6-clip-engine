# ARO-CHAT-0330 — reject in-place output mutation during smoke hashing

- Exact title: ARO-CHAT-0330 | Reject In-Place Smoke Output Mutation.
- Workstream: ARO-GTA-P0-330; continuation of existing draft PR #386 on its original branch and base.
- Static review found that the output verifier already compared file identity and metadata before/after hashing, but had no focused regression proving that same-inode, same-size in-place content mutation during the read is rejected.
- Added a regression that mutates the first 4 KiB of a 2 MiB synthetic output after the first read chunk. The verifier must fail because the file metadata changes during hashing.
- Test commit: `7fc932930afa93c6a32844e1b13a5c6e9e6d4064`.
- Tests NOT RUN in this connector session. Synthetic FFmpeg end-to-end NOT RUN. Exact-head Ubuntu/Windows CI NOT VERIFIED. No workflow dispatch/retry.
- No GTA 6 media processed. PR #386 remains OPEN / DRAFT / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. No merge, rebase, retarget, OAuth, credentials, upload, publishing, or deployment.
