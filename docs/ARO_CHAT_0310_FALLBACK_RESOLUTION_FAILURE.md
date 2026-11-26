# ARO-CHAT-0310 — contain terminal fallback path-resolution failures

## Finding

Static review found that `_write_exclusive_terminal_fallback()` called `Path.resolve()` for the fallback and protected source/output paths before opening the fallback file. A symlink loop or malformed path can raise `RuntimeError` or `ValueError`, while the caller's fallback failure handler catches only `OSError`.

On the terminal-report path, this could let the resolution exception escape to the outer generic report handler after rendering had already completed. The operator would lose the explicit warning to inspect a potentially completed output before retrying.

## Change

- Convert `OSError`, `RuntimeError`, and `ValueError` raised during fallback/protected-path resolution into a descriptive `OSError`.
- Keep the error inside the existing fallback failure handler, which reports both the failed fallback and the need to inspect output manually.
- Compare the resolved fallback path against a tuple of resolved protected paths after successful validation.
- Add an end-to-end regression that simulates a completed render, a partial terminal-report write, and a fallback path resolution failure. It asserts the output is preserved and the operator receives the manual-inspection warning.
- No uploader, OAuth, publishing, source-media, or render behavior changes.

## Commits

- Production: `d17f71d1b19ea0848e655bde41a08846585317c2`
- Regression: `d6a46a7dbfc6a67c562adbab2dec170095217f41`

The commit messages retain a provisional 0309 label from the initial reservation attempt. The startup handoff already contained a separate ARO-CHAT-0309 task, so canonical attribution for this change is ARO-CHAT-0310 / ARO-GTA-P1-310. No commit history was rewritten.

## Validation

- Regression added: `test_cli_fallback_resolution_error_keeps_output_inspection_warning`.
- Tests NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED.
- Independent review NOT RECORDED.
- Owner-device Windows verification NOT VERIFIED.
- No real authorized MP4 processed.

## Safety

Continues on existing PR #386 and branch `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`. Preserve its original base and ancestry, OPEN / DRAFT / UNMERGED state. No merge, rebase, retarget, workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
