# ARO-CHAT-0248 — Stable source snapshot mutation regression

- Exact chat title: `ARO-CHAT-0248 | Test Stable Snapshot Mutation Guard`
- Workstream: ARO-GTA-P1-248
- Follow-up to: PR #386 / ARO-GTA-P1-244; existing branch and ancestry preserved.
- Finding: the stable snapshot copier verifies descriptor and pathname metadata after copying, but the regression suite did not directly prove that an in-place source mutation during the multi-chunk copy removes the partial snapshot and fails closed.
- Change: add a regression that mutates a selected 2 MiB source after the first bounded read and asserts the snapshot operation raises and leaves no snapshot behind. Add a symlink-source regression for the snapshot boundary.
- Test commit: `af6e70f15b97714ecc08cc816c8e610a41d1b06f`.
- Repository tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- No real media processed, no OAuth or credentials, no upload/publishing, no workflow retry/dispatch, no merge/rebase/retarget/deployment.
- PR #386 remains DRAFT / OPEN / UNMERGED. Preserve the existing ancestry; PR #379 conflicts with the one-selected-video requirement.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled.
