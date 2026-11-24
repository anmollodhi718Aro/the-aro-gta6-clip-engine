# ARO-CHAT-0207 | Restore case-insensitive destination-profile isolation

**Date:** 2026-11-24  
**Chat ID:** ARO-CHAT-0207  
**Workstream ID:** ARO-GTA-P1-207  
**Repository:** `anmollodhi718Aro/the-aro-gta6-clip-engine`  
**Role:** Security regression fix on consolidated private-upload branch

## Finding

Independent review of PR #311 head `c3d767fd055c80dbd395c5c8821a335ad9b3b258` found that destination-profile names were no longer checked for case-insensitive uniqueness. Because token filenames are derived from the profile name, names such as `aroanmol7` and `AROANMOL7` can collide on case-insensitive filesystems and undermine per-profile OAuth token isolation.

## Change

- Restore a `casefold()` uniqueness set in `load_destination_profile()`.
- Fail closed with a clear `PermissionError` when profile names collide without regard to case.
- Add `test_case_colliding_profile_names_fail_closed`, which creates two case-colliding profile keys and asserts rejection.
- No OAuth credentials, token contents, real media, upload behavior, or publishing permissions were accessed or changed.

## Branch and ancestry

- Branch: `workstream/aro-chat-0207-casefold-profile-isolation-fix-2026-11-24`
- Base: PR #311 head `c3d767fd055c80dbd395c5c8821a335ad9b3b258`
- Parent PR: [#311](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/311)
- Scope: one uploader validation guard, one regression test, and continuation documentation.

## Validation

- Local tests in this connector session: NOT RUN.
- This follow-up branch's exact-head Ubuntu and hosted-Windows CI: PENDING.
- CI evidence from PR #311 does not apply to this new head.
- Independent review finding is addressed in code but requires fresh CI and independent review.

## Safety and remaining gates

- PR #311 remains OPEN / DRAFT / UNMERGED; this branch is a draft follow-up only.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
- Keep live uploads and public publishing disabled. Real OAuth/channel verification, owner-device verification, rights review, and a separately authorized PRIVATE staging acceptance remain outstanding.
- No merge, rebase, retarget, deployment, OAuth session, credential access, real-media upload, public publishing, or destructive action was performed.
