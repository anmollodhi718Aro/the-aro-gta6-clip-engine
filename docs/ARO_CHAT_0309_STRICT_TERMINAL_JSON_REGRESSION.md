# ARO-CHAT-0309 — strict terminal JSON serialization regression

## Finding

The renderer CLI already rejects non-finite direct clip bounds before reserving its RUNNING report, and uses `json.dumps(..., allow_nan=False)` for initial and terminal report serialization. The existing regression covered NaN and infinities in CLI bounds, but did not exercise the second serialization boundary: malformed/non-finite metadata returned by a media-processing boundary.

Without a regression at that boundary, a future change could accidentally re-enable Python's non-standard `NaN` / `Infinity` JSON tokens or modify the reserved report before serialization has succeeded.

## Change

Added `test_cli_preserves_strict_running_report_when_terminal_json_contains_nan` to `tests/test_single_clip_render.py`.

The test supplies a mocked renderer result containing a NaN metadata value, then verifies:
- the CLI returns its failure code;
- the already-reserved report remains parseable by a strict JSON parser that rejects non-standard constants;
- the report remains in the honest `RUNNING` state rather than persisting malformed terminal JSON;
- no output file is created; and
- the renderer boundary is invoked exactly once.

This is test-only. No production renderer, report-writing, media, rights-gate, or upload behavior was changed.

## Attribution

- Chat ID: ARO-CHAT-0309
- Exact chat title: ARO-CHAT-0309 | Strict Terminal JSON Serialization Regression
- Workstream ID: ARO-GTA-P1-309
- Existing branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Existing draft PR: #386
- Test commit: `72b8270ab41d2c7309808657a20045f1eaa9ded3`

## Validation and safety

- Test execution: NOT RUN in this connector session.
- Exact-head Ubuntu / hosted-Windows CI: NOT VERIFIED; inspect the new commit's own Actions run before claiming a pass.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Real authorized media: NOT PROCESSED / NOT VERIFIED.
- No OAuth, credentials, real media, upload, publishing, workflow retry/dispatch, merge, rebase, retarget, or deployment occurred.
- PR #386 remains OPEN / DRAFT / UNMERGED. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Live uploads and public publishing remain disabled.
