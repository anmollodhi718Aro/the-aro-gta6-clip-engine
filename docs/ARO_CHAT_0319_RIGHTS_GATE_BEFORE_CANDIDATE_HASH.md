# ARO-CHAT-0319 — require rights confirmation before candidate media hashing

- Chat ID: ARO-CHAT-0319
- Workstream: ARO-GTA-P0-319
- Continued existing draft PR #386 and branch `workstream/aro-chat-0244-single-selected-clip-render-2026-11-25`; no duplicate branch or PR.
- Static review found that candidate-CSV CLI mode hashed the entire selected source before calling the renderer. The renderer's own `--execute` rights gate already blocked before FFprobe/snapshot creation, but the CLI-side digest check still read selected-media bytes without `--confirm-rights`.
- The candidate hashing stage is now skipped for `--execute` requests lacking rights confirmation. The renderer returns a durable BLOCKED result; direct internal renderer entry also checks the rights gate before source identity/preflight work.
- Added regression coverage for direct API and candidate-CSV CLI paths: no source hashing, FFprobe, snapshot, FFmpeg, or output occurs without rights confirmation.
- Production commit: `1ecba6c0de0d20ef019658e3ce64a8500b9fb254`.
- Regression commit: `87feece9b1cebe6d8bbc2e8b6ab03146eac499f9`.
- Tests NOT RUN in this connector session. Exact-head Ubuntu/hosted-Windows CI NOT VERIFIED. Independent review NOT RECORDED. Owner-device Windows verification NOT VERIFIED. Authorized real MP4 NOT PROCESSED.
- Preserve PR #386 OPEN / DRAFT / UNMERGED and its original base/ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL.
