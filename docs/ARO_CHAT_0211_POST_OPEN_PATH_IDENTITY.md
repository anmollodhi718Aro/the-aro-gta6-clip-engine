# ARO-CHAT-0211 | Post-open approval-path identity verification

Date: 2026-11-24

## Finding
The approval reader compared the pre-open `lstat()` identity with the opened descriptor's `fstat()` identity and used `O_NOFOLLOW` where available. On a platform without `O_NOFOLLOW`, a pathname could be replaced with a symlink to the same inode between the initial check and open. The descriptor identity would still match, while the pathname itself had become a symlink.

## Change
- After opening and validating the descriptor, perform a second `lstat()` on the pathname.
- Require the post-open pathname to remain a regular file.
- Require its device/inode identity to match the opened descriptor.
- Add a regression test that simulates a platform without `O_NOFOLLOW` and replaces the checked path with a symlink to the same inode.
- Preserve the existing pre-open checks, descriptor identity check, non-blocking open, and descriptor cleanup.
- Portability follow-up skips the symlink-specific test only when symlink creation is unavailable.

## Workstream
- Chat ID: ARO-CHAT-0211
- Exact title: ARO-CHAT-0211 | Post-Open Approval-Path Identity Verification
- Workstream ID: ARO-GTA-P1-211
- Branch: `workstream/aro-chat-0211-post-open-approval-path-identity-2026-11-24`
- Base / starting SHA: PR #317 head `36f9ac70f841715255d917183d24d3b2df2bfc49`
- Parent: PR #317
- Source commit: `07fc209ff4d68b7cc5236c834bcea42de95728f3`
- Test commit: `b37b3d694c4e6dc7f3c291a242f925dabdd0bc3e`
- Portability commit: `d37681e6af75b6ff81da2c47c67cf2001fb55049`

## Validation
- Commit-associated workflow lookup for source and test commits: no runs returned.
- Exact final-head Ubuntu and hosted-Windows CI: PENDING.
- Local tests: NOT RUN.
- Owner-device Windows verification: NOT VERIFIED.
- Real GTA 6 media: NOT USED; real-media acceptance NOT VERIFIED.

## Identity correction
The initial work branch used ARO-CHAT-0210, already assigned to a separate PR #318 CI-audit workstream. The active attribution is corrected to the next unused ID, ARO-CHAT-0211. The original branch remains preserved unchanged.

## Safety
Draft-only security follow-up stacked on PR #317. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. No OAuth, credentials/tokens, network upload, publishing, merge, rebase, retarget, deployment, or destructive action. Keep live uploads and public publishing disabled pending complete independent review, owner-controlled integration, owner-device verification, and separately authorized real-media PRIVATE acceptance.
