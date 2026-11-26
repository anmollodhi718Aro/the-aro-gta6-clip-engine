# ARO-CHAT-0350 | Structured CLI Failure and Cleanup on Synthetic Fixture Timeout

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-350
- Parent: existing draft PR #386; original branch and base preserved.
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Scope: regression coverage for the operator-facing CLI timeout path during generated synthetic fixture creation.

## Change

Added `test_main_emits_structured_failure_and_cleans_up_when_fixture_generation_times_out` to `tests/test_synthetic_single_clip_smoke.py`.

The test injects `subprocess.TimeoutExpired` from the synthetic FFmpeg fixture-generation subprocess and exercises the public `main()` entry point. It verifies exit code 1, parseable JSON status `FAIL`, a structured timeout error, upload and publishing false, no renderer invocation, and cleanup of the temporary directory.

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

## Serial collision reconciliation

Concurrent continuations reserved ARO-CHAT-0346, 0347, 0348 and 0349 for separate FIFO, renderer-safety, missing-output and upload/publishing guard work. This timeout continuation is uniquely attributed to ARO-CHAT-0350 / ARO-GTA-P0-350. The regression test commit is retained; no commit history was rewritten. Earlier provisional report aliases `docs/ARO_CHAT_0347_SYNTHETIC_FIXTURE_TIMEOUT_CLI_REGRESSION.md` and `docs/ARO_CHAT_0348_SYNTHETIC_FIXTURE_TIMEOUT_CLI_REGRESSION.md` are historical aliases only.

## Safety

Preserve PR #386 OPEN / DRAFT / UNMERGED and its original branch/base/ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, deployment, or destructive action was performed. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
