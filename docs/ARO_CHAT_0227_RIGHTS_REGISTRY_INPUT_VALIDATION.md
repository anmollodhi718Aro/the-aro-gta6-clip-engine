# ARO-CHAT-0227 | Rights Registry Input Validation

## Identity
- Chat ID: ARO-CHAT-0227
- Workstream ID: ARO-GTA-P1-227
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Branch: `workstream/aro-chat-0227-rights-registry-input-validation-2026-11-25`
- Base: PR #355 branch `workstream/aro-chat-0226-rights-grant-no-overwrite-2026-11-24`
- Starting SHA: `ac95ccc7e3eda5ab83621bb4652c24cecf873d8e`

## Finding
`SourceRightsRegistry.register()` treated `allowed_uses` and `platforms` as generic iterables and stringified their members. A scalar string could therefore be interpreted character-by-character, while malformed members could be coerced into persisted permission metadata. A non-string actor could raise an incidental AttributeError instead of a deliberate validation error.

## Changes
- Require `allowed_uses` and `platforms` to be list, tuple, set, or frozenset collections.
- Require every scope/platform member to be a non-empty string.
- Reject empty collections and scalar strings.
- Require actor to be a non-empty string.
- Preserve the existing INSERT-only immutable grant behavior and authorization semantics.

## Commits
- Production: `ed13ef9d49a8829c87d6cb28b750c6cfe854bc13`
- Tests: `14e0c8ab9a3c2069aa2e7301222731460b77e6b9`
- Registry: `aed8f55e4157be56291c77750b452385e91a4274`
- Startup handoff: `267ee14d3fd7b38fe7fff0bb00ed40840e6a73b0`

## Validation
- Local tests: NOT RUN in this connector session.
- Exact-head Ubuntu CI: PENDING / NOT VERIFIED.
- Exact-head hosted-Windows CI: PENDING / NOT VERIFIED.
- Independent security review: NOT RECORDED.
- Owner-device Windows and authorized real-media acceptance: NOT VERIFIED.

## Safety
Draft only. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. No OAuth, credentials/tokens, real media, network upload, publishing, workflow retry/dispatch, merge, rebase, retarget, deployment, or destructive action. Keep live uploads/public publishing disabled.
