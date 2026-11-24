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


## Follow-up hardening — preserve token-path PermissionError (2026-11-24)
- Review found that `_read_oauth_token_info` raises `PermissionError` for path-integrity failures, but the first version of `_authorize_google` caught it through the broader `OSError` handler and could fall through to an interactive OAuth login.
- Added an explicit `except PermissionError: raise` before the generic corrupt/unreadable-credential fallback. A mocked regression proves a token-integrity error is propagated and `InstalledAppFlow.from_client_secrets_file` is not called.
- Follow-up production commit: `f7a38f535049dbf951d852caa95ad40c1aadbf62`; follow-up test commit: `08a351a88ade454c5de89098dd1a9e29cdfc818c`.
- Current code/test head: `08a351a88ade454c5de89098dd1a9e29cdfc818c`. Exact-head run #45437884661 is IN PROGRESS; the prior run #45437477812 was cancelled during branch updates and is not validation.
- No real OAuth token/client secret, login, media, network upload, or publishing was used. PR #342 remains draft/open/unmerged; Issue #68 remains OPEN.


## Exact-head CI closeout — 2026-11-24
- Code/test head `08a351a88ade454c5de89098dd1a9e29cdfc818c` passed commit-associated run [#45437884661](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/actions/runs/45437884661).
- Ubuntu job `138600745960`: compile passed; 356 tests passed; synthetic MP4/FFprobe passed.
- Hosted-Windows job `138600745153`: compile passed; the same 356-test suite ran, 3 FIFO-only tests skipped because `os.mkfifo` is unavailable; synthetic MP4/FFprobe passed.
- Both jobs checked out merge ref `4f1ffa8` (PR #342 head merged into base `6204a3979b8753919e3f983ce42a3777b3215d87`). Raw-head-only checkout NOT DEMONSTRATED. This is 356 tests per platform, not 712 unique tests.
- Logs confirm synthetic-only media (`gta6_footage_used=false`, `third_party_media_used=false`), `upload_performed=false`, `publishing_enabled=false`, `manual_review_required=true`. No real OAuth token, client secret, login, network upload, or publishing.
- Subsequent commits update only the report, startup handoff, and registry. The resulting documentation-only tip has no associated run returned and is NOT independently CI-VERIFIED; no application code or tests changed after the green code/test head.
- PR #342 remains OPEN/DRAFT/UNMERGED. Independent security review of the full consolidated uploader/approval lineage is NOT RECORDED. Issue #68 remains OPEN; keep live uploads/public publishing disabled.
