# ARO-CHAT-0332 | Keep Non-JSON Renderer Failures Structured

- Chat ID: ARO-CHAT-0332
- Exact chat title: ARO-CHAT-0332 | Keep Non-JSON Renderer Failures Structured
- Workstream ID: ARO-GTA-P0-332
- Starting observed branch head: `9da84fd1bd65bd3087a6f6090b7de58885550687`
- Existing branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Existing PR: #386, OPEN / DRAFT / UNMERGED; original base and ancestry preserved.
- Scope: ensure a malformed renderer report that cannot be JSON-serialized still produces the smoke CLI's normal structured FAIL response.

## Finding

The smoke harness correctly rejected a non-RENDERED report, but it directly serialized the report while constructing the RuntimeError. A dictionary containing a non-JSON-serializable value could raise TypeError before the CLI error handler received the intended RuntimeError, leaking an unstructured traceback instead of the standard JSON failure payload.

## Changes

- Guard renderer-report serialization against TypeError and ValueError.
- Use a fixed, non-sensitive fallback summary when the report is not valid JSON.
- Add a CLI regression with a deliberately non-serializable object in the renderer report. It asserts exit code 1, valid structured JSON on stderr, status FAIL, and upload/publishing false.
- No workflow dispatch/retry, new branch, or new PR.

## Commits

- Production guard: `8a15de2932a10da2b48b70b29ac6e3ceaaf80403`
- Regression test: `400824bdbce0076f5f1ca5b0f7ceadd61bcb43c9`
- Report: `docs/ARO_CHAT_0332_NON_JSON_RENDERER_REPORT.md`

## Validation

- Active-branch production source re-read: IMPLEMENTED.
- Active-branch regression source re-read: IMPLEMENTED.
- Local unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED / NOT VERIFIED.

## Safety and scope

Synthetic test-only path. No real or third-party footage, OAuth, credentials, upload, publishing, deployment, merge, rebase, retarget, or workflow retry/dispatch. Keep PR #386 OPEN / DRAFT / UNMERGED and preserve its original base/ancestry. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
