# ARO-CHAT-0349 | Preserve Structured CLI Failure on Overflow

- Date: 2026-11-26
- Workstream: ARO-GTA-P0-349; continuation of existing draft PR #386.
- Branch/base preserved: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25` / existing PR base.
- Finding: the synthetic single-clip smoke CLI omitted `OverflowError` from its expected operational exception boundary. An overflow escaping the renderer could print a traceback instead of the structured JSON `FAIL` response.
- Production change: catch `OverflowError` alongside existing expected CLI failure classes. No rendering, selection, authorization, upload, or publishing behavior changed.
- Regression: `test_main_emits_structured_failure_for_overflow` injects an overflow and asserts exit code 1, parseable JSON status `FAIL`, exception context, and upload/publishing false.
- Production commit: `a6e08c80b2c34dfc9920e422a6b65ad96552abf2`.
- Test commit: `b898a49f55769f531e7d9e6a21a4069899c03840`.
- IDs 0345–0348 were already assigned to concurrent synthetic CLI regressions; this task is uniquely attributed to ARO-CHAT-0349. Existing implementation/test commits are retained.
- Tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED. No workflow dispatch/retry, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
