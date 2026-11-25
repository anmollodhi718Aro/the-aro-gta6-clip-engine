# ARO-CHAT-0249 | Stable snapshot path-replacement regression

- Date: 2026-11-25
- Workstream: ARO-GTA-P1-249
- Parent: PR #386 / ARO-GTA-P1-244
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Scope: test-only follow-up; preserve the existing PR and ancestry.

## Finding and change

The stable snapshot copier already compared descriptor metadata and the selected pathname after copying, but regression coverage only exercised in-place mutation. Added a focused test that replaces the selected pathname with a different regular file while the descriptor-backed copy is in progress. The test asserts that snapshot creation fails closed, the partial snapshot is removed, the original opened file remains identifiable, and the replacement pathname is not silently accepted.

- Test: `test_snapshot_fails_closed_when_selected_path_is_replaced_during_copy`
- Test commit: `f344d134ad0d330366a0d7fb2b0dac785a9dfff9`
- Production code unchanged.

## Validation

- Repository tests: NOT RUN in this connector session.
- Exact-head Ubuntu / hosted-Windows CI: NOT VERIFIED; inspect the exact current PR head for associated runs and visible job logs.
- Independent review: NOT RECORDED.
- No real media was processed.

## Safety and ancestry

- PR #386 remains DRAFT / OPEN / UNMERGED.
- Preserve the existing #383 -> #380/#379 ancestry. PR #379 conflicts with the later one-selected-video owner requirement; do not merge, rebase, retarget, or integrate without explicit owner approval.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
- No OAuth, credentials, upload, publishing, workflow retry/dispatch, merge, rebase, retarget, or deployment was performed.
