# ARO-CHAT-0308 — finite clip bounds and strict JSON reports

## Finding

Python's `argparse` float conversion accepts `nan`, `inf`, and `-inf`. The CLI previously allowed those values into initial and terminal reports. Python's default JSON encoder emits non-standard `NaN` and `Infinity` tokens, so a report could appear complete while strict JSON parsers rejected it.

## Change

- Reject non-finite direct `--start` and `--end` values before report reservation or media inspection.
- Serialize both initial and terminal reports with `allow_nan=False`, providing a second fail-closed boundary if a non-finite value enters report metadata from a later processing stage.
- Add a CLI regression for NaN, positive infinity, and negative infinity, asserting exit code 2, no report reservation, and no output creation.
- Update the operator guide, canonical registry, and startup handoff.

## Validation

- Regression added: `test_cli_rejects_non_finite_clip_bounds_before_report_reservation`.
- Tests were NOT RUN in this connector session.
- Exact-head Ubuntu/hosted-Windows CI is PENDING / NOT VERIFIED.
- Independent review is NOT RECORDED.
- No real media was processed.

## Safety

Continues on existing PR #386 and its existing branch/base. No merge, rebase, retarget, workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
