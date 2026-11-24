# ARO-CHAT-0210 | Post-open approval-path identity verification

Date: 2026-11-24

## Finding
The approval reader compared the pre-open `lstat()` identity with the opened descriptor's `fstat()` identity and used `O_NOFOLLOW` where available. On a platform without `O_NOFOLLOW`, a pathname could be replaced with a symlink to the same inode between the initial check and open. The descriptor identity would still match, while the pathname itself had become a symlink.

## Change
- After opening and validating the descriptor, perform a second `lstat()` on the pathname.
- Require the post-open pathname to remain a regular file.
- Require its device/inode identity to match the opened descriptor.
- Add a regression test that simulates a platform without `O_NOFOLLOW` and replaces the checked path with a symlink to the same inode.
- Preserve the existing pre-open checks, descriptor identity check, non-blocking open, and descriptor cleanup.

## Workstream
- Chat ID: ARO-CHAT-0210
- Exact title: ARO-CHAT-0210 | Post-Open Approval-Path Identity Verification
- Workstream ID: ARO-GTA-P1-210
- Branch: `workstream/aro-chat-0210-post-open-path-identity-check-2026-11-24`
- Base / starting SHA: PR #317 head `36f9ac70f841715255d917183d24d3b2df2bfc49`
- Parent: PR #317
- Source commit: `07fc209ff4d68b7cc5236c834bcea42de95728f3`
- Test commit: `b37b3d694c4e6dc7f3c291a242f925dabdd0bc3e`

## Validation
- Local tests: NOT RUN.
- Exact-head Ubuntu and hosted-Windows CI: PENDING.
- Owner-device Windows verification: NOT VERIFIED.
- Real GTA 6 media: NOT USED; real-media acceptance NOT VERIFIED.
- No OAuth, credentials/tokens, network upload, publishing, merge, rebase, retarget, deployment, or destructive action.

## Safety
Draft-only security follow-up stacked on PR #317. Keep PR #317 and its parent chain open/unmerged. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled pending complete independent review, owner-controlled integration, owner-device verification, and separately authorized real-media PRIVATE acceptance.


## Cross-platform test compatibility follow-up
- Test commit `d37681e6af75b6ff81da2c47c67cf2001fb55049` makes the symlink-race regression skip only when the host filesystem cannot create symlinks, matching the existing suite's platform-aware behavior. The test still simulates the no-`O_NOFOLLOW` fallback where symlink creation is supported.
