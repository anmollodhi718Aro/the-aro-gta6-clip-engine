# ARO-CHAT-0224 — Independent uploader security lineage audit

Date: 2026-11-24

## Identity and scope
- Chat ID: ARO-CHAT-0224
- Workstream: ARO-GTA-P1-224
- Branch: `workstream/aro-chat-0224-independent-uploader-security-lineage-audit-2026-11-24`
- Base / starting SHA: `b6d712a6438a132c3d8ca245b0a804bf8b929550` (PR #350 documentation tip)
- Scope: documentation-only independent review of the PR #342 OAuth-token hardening and PR #344 current-rights-report revalidation lineage. No application code or workflow configuration changed.

## Verified evidence
- PR #350 branch exact head `b6d712a6438a132c3d8ca245b0a804bf8b929550` has commit-associated Actions run #45442036637. Both `tests` (Ubuntu) and `windows-tests` completed successfully. The jobs include compile, complete unit-test suite, and synthetic MP4/FFprobe steps. This verifies that branch head only; it does not establish raw-head-only checkout or real-media acceptance.
- PR #344 production commit `56685d4edf88af8d15b2390283752792984427a5` re-reads the rights report immediately before `youtube.videos().insert`, checks exact clip/source IDs, and re-authorizes source-bound assets. Test commit `70b86a1ead7f3f4c6c466dc79684041aac08ea18` mutates the report to add an unregistered source and asserts the API insert is not called.
- PR #344 branch file `backend/app/youtube_upload.py` still implements OAuth token loading with `Credentials.from_authorized_user_file(str(token_path), IDENTITY_SCOPES)` after a pathname `is_symlink()` check. That library call reopens the path, leaving a check/open substitution window.
- PR #342's separate OAuth hardening line records no-follow descriptor parsing and use of `Credentials.from_authorized_user_info`; its documented validated code/test head is `08a351a88ade454c5de89098dd1a9e29cdfc818c`. The PR #344 branch inspected here does not contain that loader implementation. Therefore PR #342's token hardening must not be assumed present in PR #344 or PR #350 merely because both share the ARO-CHAT-0219 attribution.
- The per-clip approval module binds reviewer Google subject, channel, clip/source IDs, privacy, expiry and SHA-256 of the exact video snapshot; it rejects symlink/non-regular approval records and verifies descriptor/path identity before parsing.

## Security findings
1. **BLOCKER — OAuth token path race remains on PR #344 / #350 lineage.** The pre-read symlink check is not sufficient while the token is reopened by `Credentials.from_authorized_user_file`. The no-follow descriptor implementation exists on the separate PR #342 line and is not integrated into this branch.
2. **LINEAGE BLOCKER — duplicate ARO-CHAT-0219 implementations.** PR #342 and PR #344 have separate branches and different code changes under the same chat/workstream attribution. Preserve both histories. Do not merge, rebase, retarget, or claim a consolidated security implementation without owner-directed lineage selection and a fresh independent review.
3. **RESIDUAL LIMITATION — local rights evidence is not legal verification.** The rights registry explicitly stores operator-supplied evidence metadata and cannot authenticate the grantor or decide legal sufficiency. Human verification of source/asset permissions remains required.
4. **ACCEPTANCE BLOCKER — no live acceptance.** OAuth/device verification, authorized real-media review, real private-upload confirmation, and independent review of the consolidated lineage remain unverified. Synthetic CI is not real-media or upload evidence.

## Required next actions
- Keep PRs draft/open/unmerged and public publishing disabled.
- Owner must select the canonical PR #342 / PR #344 lineage or authorize a dedicated consolidation branch.
- On the owner-selected branch, integrate the no-follow OAuth token reader, add/retain regressions for path substitution and no interactive OAuth fallback, and run fresh exact-head Ubuntu/Windows CI.
- Independently review the resulting full uploader/approval diff before any owner-controlled local acceptance.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. No OAuth login, secrets access, real media, API upload, workflow retry/dispatch, merge, rebase, retarget, deployment, or publishing was performed in this audit.

## Status
- Documentation audit: IMPLEMENTED.
- PR #350 exact-head CI: CI_VERIFIED for run #45442036637, both jobs successful.
- Consolidated security implementation: BLOCKED pending owner lineage decision and token-loader integration.
- Real-media / owner-device / live PRIVATE upload acceptance: NOT VERIFIED.
