# ARO-CHAT-0347 | Structured CLI Failure and Cleanup on Synthetic Fixture Timeout

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-347
- Parent: existing draft PR #386; original branch and base preserved.
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Scope: regression coverage for the operator-facing CLI timeout path during generated synthetic fixture creation.

## Change

Added `test_main_emits_structured_failure_and_cleans_up_when_fixture_generation_times_out` to `tests/test_synthetic_single_clip_smoke.py`.

The test injects `subprocess.TimeoutExpired` from the synthetic FFmpeg fixture-generation subprocess and exercises the public `main()` entry point. It verifies:
- exit code is 1;
- stderr contains parseable JSON with status `FAIL`;
- the timeout is represented in the structured error;
- upload and publishing remain false;
- the renderer is never invoked; and
- the temporary directory is removed after the timeout.

Production code unchanged. The existing `subprocess.SubprocessError` exception boundary is expected to handle `TimeoutExpired`.

## Commit

- Regression test commit: `1e1313bbaaa25fb82f1d3abca3e9410c4dc8afd4`
- Changed file: `tests/test_synthetic_single_clip_smoke.py`

## Validation

- Static change/read-back: PRESENT on the active branch.
- Local unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Serial and safety controls

ARO-CHAT-0346 was concurrently assigned to a separate missing-output regression. This continuation is uniquely attributed to ARO-CHAT-0347 / ARO-GTA-P0-347; no commit history was rewritten. The regression test commit is retained.

Preserve PR #386 OPEN / DRAFT / UNMERGED and its original branch/base/ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, deployment, or destructive action was performed. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
