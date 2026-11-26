# ARO-CHAT-0327 | Stable Synthetic Output Identity Verification

Date: 2026-11-26

## Attribution
- Chat ID: ARO-CHAT-0327
- Workstream ID: ARO-GTA-P0-327
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Existing draft PR: #386
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Base: preserved unchanged from PR #386

## Finding
The synthetic smoke harness independently compared the renderer's SHA-256 with the output bytes, but its verification used a normal path-based open. A replaced output path or symlink could cause the harness to hash a different file than the one whose path was initially checked. The reported output size was also read separately after hashing.

## Changes
- Added `_hash_verified_output()` to reject symlinks and non-regular files.
- Opened the output with non-following flags where supported, plus nonblocking open where available.
- Compared path and descriptor identity before and after streaming the bytes through SHA-256.
- Returned the byte count from the same verified descriptor used for the digest.
- Added tests for symlink rejection and matching digest/size from the same file.
- No renderer production behavior was changed.

## Commits
- Initial helper and tests: `a9a7443d094a860d5e52645caeae8f98ae7fa00d`, `9bb5940e325307a878e1d5e956b1c75421e8fdaf`.
- Nonblocking-open hardening: `e9ecfd5e3e0000ab914cc7e19c414a0c2a1ddb90`.

## Verification
- Source and regression tests re-read from the current branch.
- Unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end smoke: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED / NOT VERIFIED.

## Safety and handoff
- Continued existing PR #386; no new PR or branch.
- PR #386 remains OPEN / DRAFT / UNMERGED; original base and ancestry preserved.
- No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep public publishing disabled.
