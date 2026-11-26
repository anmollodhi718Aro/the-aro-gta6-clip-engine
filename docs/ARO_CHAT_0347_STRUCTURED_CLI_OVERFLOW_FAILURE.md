# ARO-CHAT-0347 | Preserve Structured CLI Failure on Overflow

- Date: 2026-11-26
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Workstream: ARO-GTA-P0-347; continuation of existing draft PR #386.
- Branch/base preserved: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25` / existing PR base.
- Finding: the synthetic single-clip smoke CLI converted expected operational exceptions into structured JSON `FAIL` output, but its exception boundary omitted `OverflowError`. An overflow escaping the renderer could therefore print a traceback instead of the stable operator-facing failure contract.
- Production change: catch `OverflowError` alongside the existing expected CLI failure classes. No rendering, selection, authorization, upload, or publishing behavior changed.
- Regression: `test_main_emits_structured_failure_for_overflow` injects an overflow from the selected-clip renderer and asserts exit code 1, parseable JSON status `FAIL`, the exception context, and upload/publishing false.
- Production commit: `a6e08c80b2c34dfc9920e422a6b65ad96552abf2`.
- Test commit: `b898a49f55769f531e7d9e6a21a4069899c03840`.
- Initial report/attribution commits used colliding IDs 0345 and 0346; corrected attribution is ARO-CHAT-0347. No implementation or test history was rewritten.
- Tests: NOT RUN in this connector session.
- Exact-head CI: NOT VERIFIED; exact-head workflow lookup returned no workflow runs.
- Independent review: NOT RECORDED.
- Synthetic FFmpeg end-to-end: NOT RUN.
- Owner-device Windows verification: NOT VERIFIED.
- Authorized real GTA 6 MP4: NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED. Do not dispatch/retry workflows, merge, rebase, retarget, use OAuth/credentials, process real media, upload, publish, or deploy. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.

## Serial collision reconciliation

ARO-CHAT-0345 and ARO-CHAT-0346 were already reserved by concurrent continuations for separate synthetic CLI regressions. This overflow-handling continuation is uniquely attributed to ARO-CHAT-0347 / ARO-GTA-P0-347. Existing implementation and test commits are retained; no history was rewritten.
