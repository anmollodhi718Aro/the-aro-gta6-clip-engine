# ARO-CHAT-0314 — identify interrupted single-clip render invocations

- Date: 2026-11-26
- Workstream: ARO-GTA-P1-314
- Continued existing draft PR #386 and branch `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`; no new branch or PR.

## Static review finding

The renderer durably reserves a strict-JSON `RUNNING` report before media inspection and rendering. This safely prevents a second invocation from overwriting the reservation, but a hard process termination can leave the report in `RUNNING` indefinitely. The report previously lacked a unique invocation identifier and process start metadata, making manual triage less precise.

There is no safe automatic stale-run detector: a process may still be active, PIDs can be reused, and a completed or partial output may already exist. Automatically converting `RUNNING` to `FAIL` or resuming a render would risk misreporting or duplicating work.

## Changes

- Initial durable reports now include a UUID `run_id`, timezone-aware `started_at_utc`, and diagnostic `process_id`.
- Terminal and fallback reports inherit these fields from the initial reservation.
- The operator guide now documents a fail-closed interrupted-run procedure: preserve report evidence, confirm process termination using more than PID alone, inspect possible output, and use new report/output paths only after manual review.
- No automatic recovery, report mutation, stale-process inference, or rerender behavior was added.

## Validation

- Added assertions to the existing candidate CLI reservation-order regression for run ID format, UTC timestamp offset, and positive process ID.
- Local tests NOT RUN in this connector session.
- Exact-head Actions CI NOT VERIFIED at the time of this change.
- Independent review NOT RECORDED.
- Owner-device Windows verification NOT VERIFIED.
- Authorized real MP4 NOT PROCESSED.

## Safety

Preserve PR #386 OPEN / DRAFT / UNMERGED and its original base/ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.


## Follow-up regression coverage

- The terminal-success report regression now verifies that `run_id`, `started_at_utc`, and `process_id` survive the RUNNING-to-terminal report transition.
- The terminal-serialization fallback regression now verifies that the separate fallback carries the exact same invocation identity as the preserved primary RUNNING report.
- Follow-up test commits: `be7aa98b0066d43ce3349da5ed6eb7345bb1dd57` and `babe0322d7928585b8d83e61f959070ba5fad862`.
- Tests remain NOT RUN in this connector session; exact-head CI remains NOT VERIFIED.
