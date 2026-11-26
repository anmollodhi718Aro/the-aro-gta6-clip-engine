# ARO-CHAT-0308 — Terminal fallback regression trigger correction

- Chat ID: ARO-CHAT-0308
- Workstream: ARO-GTA-P1-308
- Repository: `anmollodhi718Aro/the-aro-gta6-clip-engine`
- Existing PR: [#386](https://github.com/anmollodhi718Aro/the-aro-gta6-clip-engine/pull/386)
- Branch: `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`

## Finding

The expanded-report-path fallback regression configured its failure injector to return a short write on the third write to the primary report handle. The CLI performs only two writes to that handle: the durable initial RUNNING reservation, followed by the terminal report. The third write never occurs on that handle, so the test did not force the fallback branch.

## Change

Changed the injected short-write trigger from the third call to the second call. The test now targets the terminal report write and can verify the fallback-file persistence path. Production code is unchanged.

- Test commit: `ae96db84e0e466b6085b4b8ef55ddd6ac65bcc12`

## Validation

- Test execution in this connector session: NOT RUN.
- Exact-head Ubuntu/hosted-Windows CI: NOT VERIFIED.
- Independent review: NOT RECORDED.
- Owner-device Windows verification: NOT VERIFIED.
- Real authorized MP4: NOT PROCESSED / NOT VERIFIED.

## Safety

PR #386 remains OPEN / DRAFT / UNMERGED on its existing base and ancestry. No workflow retry/dispatch, OAuth, credentials, real media, upload, publishing, merge, rebase, retarget, deployment, or destructive action was performed. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL. Live uploads and public publishing remain disabled.
