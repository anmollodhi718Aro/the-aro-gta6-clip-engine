# ARO-CHAT-0326 | Verify Synthetic Smoke Failure Cleanup

Date: 2026-11-26

## Scope
- Workstream: ARO-GTA-P0-326
- Continue existing draft PR #386 on its existing branch and base.
- No duplicate branch or PR.

## Finding
The smoke harness uses TemporaryDirectory, so its generated source and output should be removed when validation fails as well as when it succeeds. Existing coverage asserted cleanup only on the successful path. A regression is needed to lock down cleanup after a digest-integrity failure.

## Change
- Add a failure-path test that captures the temporary source/output paths, makes the renderer emit a valid MP4-like test payload with an incorrect but well-formed SHA-256, asserts the harness fails closed, and verifies both temporary artifacts and their containing temporary directory are removed.
- Production behavior is unchanged; TemporaryDirectory remains responsible for cleanup.

## Verification
- Test source committed; tests NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED.
- Synthetic FFmpeg end-to-end NOT RUN.
- Independent review NOT RECORDED.
- Authorized real GTA 6 MP4 NOT PROCESSED.

## Safety and boundaries
- Synthetic bytes only; no external footage.
- No OAuth, credentials, upload, publishing, workflow retry/dispatch, merge, rebase, retarget, deployment, or destructive action.
- Keep PR #386 OPEN / DRAFT / UNMERGED and preserve its ancestry.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Public publishing stays disabled.
