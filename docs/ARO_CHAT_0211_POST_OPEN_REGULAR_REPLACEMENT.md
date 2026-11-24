# ARO-CHAT-0211 | Post-open regular-file replacement regression

Date: 2026-11-24

## Scope
Add focused regression coverage for the post-open pathname identity check in the durable owner-approval reader. The test simulates replacing the pathname with a different regular file after the descriptor has opened but before the post-open `lstat()`.

## Workstream
- Chat ID: ARO-CHAT-0211
- Exact title: ARO-CHAT-0211 | Post-Open Regular-File Replacement Regression
- Workstream ID: ARO-GTA-P1-211
- Branch: `workstream/aro-chat-0211-post-open-regular-replacement-test-2026-11-24`
- Base / starting SHA: PR #319 head `4f5796e2a62927213f474a1e09ff1927d540cf96`
- Parent: PR #319
- Changed implementation: tests only; production behavior unchanged.

## Expected behavior
The open descriptor continues to reference the original file, while the pathname points to a different regular file. The reader must reject this device/inode mismatch with the existing fail-closed error instead of accepting either file's contents.

## Validation
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu and hosted-Windows CI: PENDING.
- Owner-device Windows verification: NOT VERIFIED.
- Real-media acceptance: NOT USED / NOT VERIFIED.
- No OAuth, credentials/tokens, network upload, publishing, merge, rebase, retarget, deployment, or destructive action.

## Safety
Draft-only regression test stacked on PR #319. Keep the PR chain open/unmerged. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads and public publishing disabled.
