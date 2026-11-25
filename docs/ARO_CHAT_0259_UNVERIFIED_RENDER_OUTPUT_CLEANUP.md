# ARO-CHAT-0259 | Remove Unverified Render Outputs Safely

- Exact chat title: `ARO-CHAT-0259 | Remove Unverified Render Outputs Safely`
- Workstream: `ARO-GTA-P1-259`
- Continuation of PR #386 / ARO-GTA-P1-244 on `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`; no new branch or PR.
- Static review found that an output could remain at its final destination after post-render FFprobe failure or a duration mismatch. Because overwrite is prohibited, the stale output also blocked a safe retry.
- The renderer now captures the output's device/inode/file-type identity immediately after `render_clip()`. On verification failure it removes the output only if the destination still identifies that exact file. Replaced, symlinked, or uncertain paths are preserved.
- Regression coverage verifies removal of the invocation's own failed output and preservation of a replacement output.
- Source commit: `5379884d9996c86713987352ae6b68c78d36cd9a`; initial test commit: `cd73f6ca90da603b4c3ec14ecdf5156e5e23010e`; test follow-up: `a067f6159a3ef34336a3e562e8126a8fce6c1ed9`; deterministic replacement test: `e9e96b94f4d44255e62a046cf61046f8ba1fd43e`.
- This workstream ID was changed from 0258 to 0259 after live registry inspection found concurrent ARO-CHAT-0258 reservations. The existing branch and PR were preserved.
- Repository tests NOT RUN in this connector session. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows and authorized real-media acceptance NOT VERIFIED.
- PR #386 remains DRAFT / OPEN / UNMERGED. No merge, rebase, retarget, workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
