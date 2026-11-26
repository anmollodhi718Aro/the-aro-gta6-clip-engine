# ARO-CHAT-0318: Preserve partial terminal-fallback path evidence

## Finding

The terminal fallback writer used exclusive creation, then wrote and fsynced the sidecar. If the write was short or file-level flush/fsync raised, the sidecar could remain partially written, but the helper propagated only the underlying I/O error. The caller therefore did not receive the exact path of a file that this invocation had already created.

## Change

- Track whether exclusive creation succeeded.
- If a subsequent write, flush, or file fsync fails, raise an I/O error that names the exact fallback path and states that a partial or non-durable file may remain.
- Preserve the sidecar for manual inspection. Never overwrite or automatically delete it.
- Keep pre-creation failures distinct, so an existing fallback collision is not misreported as a newly created partial file.
- Add a regression that injects a short write, verifies the exact path appears in the error, and confirms the partial sidecar is preserved.

## Validation

- Production commit: `a4be945cd3ba20558dbf26f88bc79d7859d4eaae`
- Regression commits: `625c39443b87a4a8ab76154a8425450c4d664297`, fixture correction `6484d082b95a6e4ea09e06b54232f2f7438182e8`.
- Tests NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED.
- Independent review NOT RECORDED.
- Owner-device Windows verification NOT VERIFIED.
- No real authorized MP4 processed.

## Safety

Continues on existing PR #386 and branch `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`. Preserve OPEN / DRAFT / UNMERGED state and original ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
