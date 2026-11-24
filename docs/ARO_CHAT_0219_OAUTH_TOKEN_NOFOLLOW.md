# ARO-CHAT-0219 | Read OAuth token files through no-follow descriptors

Date: 2026-11-24

## Attribution
- Chat ID: ARO-CHAT-0219
- Workstream ID: ARO-GTA-P1-219
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- PR: #342 (DRAFT / OPEN / UNMERGED)
- Branch: `workstream/aro-chat-0219-oauth-token-no-follow-2026-11-24`
- Base: PR #339 branch `workstream/aro-chat-0218-current-head-media-cleanup-2026-11-24`
- Starting SHA: `6204a3979b8753919e3f983ce42a3777b3215d87`
- Production change: `d5f764f49645608b42dffad354bc75575fb4f0b3`
- Regression tests: `a26951f486bce4710d7a3b8a85440076870d305d`

## Finding
The OAuth loader rejected a token path that was already a symlink, but then called `Credentials.from_authorized_user_file(path)`, which reopened the pathname. A local path replacement between the symlink check and that second open could redirect token-file reads.

## Changes
- Added `_read_oauth_token_info` to open the token file with `O_NOFOLLOW` and `O_NONBLOCK` where supported.
- Require a regular file and compare device/inode identity before open, on the opened descriptor, and after open.
- Parse JSON from the already-verified descriptor and pass the resulting object to `Credentials.from_authorized_user_info`, avoiding a second pathname open.
- Reject symlinked, raced, non-regular, missing/unreadable, and non-object token files.
- Added synthetic local-file tests for valid JSON, direct symlink rejection, symlink replacement between path check and open, and directory rejection.

## Validation
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu and hosted-Windows CI: PENDING / NOT YET RETURNED for PR #342's head. Do not reuse PR #339 or the parent branch's CI.
- The tests use synthetic token JSON only. No real OAuth token, client secret, login, or credential access occurred.
- No network upload, real media, or publishing occurred.

## Safety and disposition
- PR #342 remains draft/open/unmerged.
- No merge, rebase, retarget, workflow retry/dispatch, OAuth login, credential access, real media, YouTube network upload, deployment, or publishing.
- Issue #68 remains OPEN. Keep live uploads and public publishing disabled.
- Next: inspect PR #342's own Ubuntu and hosted-Windows CI, then review the full consolidated OAuth/approval lineage and exact PR ancestry before any integration.
