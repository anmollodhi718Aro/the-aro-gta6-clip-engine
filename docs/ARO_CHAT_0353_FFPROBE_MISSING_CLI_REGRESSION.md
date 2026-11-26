# ARO-CHAT-0353 | Structured CLI Failure When FFprobe Is Missing

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-353
- Parent: existing draft PR #386; original branch and base preserved.
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`
- Scope: operator-facing CLI regression for the required FFprobe executable being unavailable.

## Change

Added `test_main_emits_structured_failure_when_ffprobe_is_missing` to `tests/test_synthetic_single_clip_smoke.py`.

The regression invokes the public `main()` entry point with FFmpeg discoverable and FFprobe missing. It verifies exit code 1, parseable JSON `FAIL`, an FFprobe-specific error, upload/publishing false, and that neither synthetic fixture generation nor clip rendering starts.

Production code unchanged.

## Commit

- Test commit: `6581ecb3d9431868667b61820e5dafde8dd7f7e6`
- Changed file: `tests/test_synthetic_single_clip_smoke.py`
- Earlier provisional report alias: `docs/ARO_CHAT_0351_FFPROBE_MISSING_CLI_REGRESSION.md` (superseded attribution only).

## Validation

- Static change/read-back: PRESENT.
- Local unit tests: NOT RUN in this connector session.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.

## Serial collision reconciliation

ARO-CHAT-0351 was already reserved by a concurrent source-alias output guard task. This FFprobe CLI regression is uniquely reassigned to ARO-CHAT-0353 / ARO-GTA-P0-353. The test commit is retained; no history was rewritten. The provisional 0351 report file remains as a historical alias only.

## Safety

Preserve PR #386 OPEN / DRAFT / UNMERGED and its original branch/base/ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads and public publishing remain disabled.
