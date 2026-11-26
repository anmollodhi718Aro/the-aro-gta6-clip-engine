# ARO-CHAT-0328 | Reject Malformed Smoke Renderer Reports

Date: 2026-11-26

## Attribution
- Chat ID: ARO-CHAT-0328
- Workstream ID: ARO-GTA-P0-328
- Existing draft PR: #386
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Base: unchanged from PR #386

## Finding
The synthetic smoke harness consumed the renderer return value as a dictionary without validating its type first. A malformed return value could escape as an unhandled attribute error instead of a controlled smoke-test failure.

## Changes
- Require the production renderer result to be a dictionary before reading status or report fields.
- Fail closed with a clear RuntimeError when the renderer returns a malformed report.
- Add a regression test for a renderer returning `None`.
- No production rendering, upload, or publishing behavior changed.

## Commits
- Production guard: `df1120bbc37d8961159ddb908914b39942bb533f`
- Regression: `ec1c7b84bc511e87ffc74cb7d0df11cb3190662e`

## Verification
- Updated source and regression test committed to the existing PR branch.
- Unit tests NOT RUN.
- Synthetic FFmpeg end-to-end smoke NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED.
- Independent review NOT RECORDED.
- Authorized real GTA 6 MP4 NOT PROCESSED / NOT VERIFIED.

## Safety
- PR #386 remains OPEN / DRAFT / UNMERGED; branch and base unchanged.
- No workflow dispatch/retry, merge, rebase, retarget, credentials, real media, upload, publishing, or deployment.
- Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
