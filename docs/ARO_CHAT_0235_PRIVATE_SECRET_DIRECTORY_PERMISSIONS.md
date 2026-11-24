# ARO-CHAT-0235 | Restrict existing OAuth secret directories

Date: 2026-11-25

## Attribution
- Workstream: ARO-GTA-P1-235
- Repository: anmollodhi718Aro/the-aro-gta6-clip-engine
- Branch: `workstream/aro-chat-0235-tighten-existing-secrets-directory-permissions-2026-11-25`
- Parent: PR #368, destination-profile OAuth bootstrap
- Starting SHA: `44625b51672221a823e98c4abf327024839a30d7`

## Finding
The destination setup used `mkdir(mode=0o700, exist_ok=True)` for `.secrets/` and `.secrets/tokens/`. The mode argument only applies when a directory is newly created. If either directory already existed with broader POSIX permissions, the setup did not tighten those permissions before placing OAuth material there.

## Change
- Added `_ensure_private_directory()` to reject a symlink or non-directory at the final path component.
- On POSIX, require current-user ownership, apply mode `0700`, and verify the resulting mode.
- Retain the existing resolved-path check to ensure the directory remains at its expected repository-local path.
- Apply the helper to both `.secrets/` and `.secrets/tokens/`.
- Add a POSIX regression test that starts with both directories at mode `0755` and verifies both are tightened to `0700`.

## Validation
- Source commit: `435acaf30b4817d00cd8194298f929807214a3e0`.
- Test commit: `66e200e9f83b256a221505e8513404c42ea35e4b`.
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI: PENDING.
- Independent security review: NOT RECORDED.
- Windows mode-bit semantics differ from POSIX; on Windows, confidentiality still depends on the user's private profile ACL. This change does not claim to create or verify Windows ACLs.

## Safety
- No OAuth flow was executed; no credentials or tokens were accessed.
- No upload, publishing, workflow retry/dispatch, merge, rebase, retarget, deployment, or destructive action.
- Parent PR #368 remains draft/unmerged. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Keep live uploads/public publishing disabled.
