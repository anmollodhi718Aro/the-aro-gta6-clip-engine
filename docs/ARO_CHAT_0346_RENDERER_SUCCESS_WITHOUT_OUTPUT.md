# ARO-CHAT-0346 | Reject Renderer Success Without a Synthetic Output File

- Workstream: ARO-GTA-P0-346.
- Continuation target: existing draft PR #386 on its original branch and base.
- Starting observed PR head before this continuation: `67e0dd9da31b5abc64cc20f0eb4f2e94c3d68eda`.
- Added `test_main_emits_structured_failure_when_renderer_reports_missing_output` to `tests/test_synthetic_single_clip_smoke.py`.
- The fake renderer reports `status=RENDERED` and a syntactically valid SHA-256 but deliberately creates no output file. The test exercises the public CLI `main()` boundary and requires exit code 1, parseable JSON `FAIL`, the explicit missing-output error, and upload/publishing remaining false.
- This complements the existing empty-output checks by separately covering a false-success report with no artifact at all.
- Production code unchanged. Test commit: `e692439af7428003e4deaf2b7488cc10e47fa784`.
- Serial collision reconciliation: ARO-CHAT-0345 was concurrently assigned to other documented tasks on this branch. This continuation is therefore uniquely assigned ARO-CHAT-0346; the original test commit is retained without history rewriting.
- Focused report commit: `cf1fa9d9c009cd10c57cac66337b9b01e9ea670f`; registry commit: `11e7cbf0139b71c7494c3ca7daf07d009ffd28ce`; startup handoff commit: `deea77e62bd9d5a64cd0d23becde555325258d97`.
- Validation: static change/read-back only. Unit tests NOT RUN; synthetic FFmpeg end-to-end NOT RUN; exact-head Ubuntu/hosted-Windows CI NOT VERIFIED; independent review NOT RECORDED; owner-device Windows verification NOT VERIFIED; authorized real GTA 6 MP4 NOT PROCESSED.
- Safety: preserve PR #386 OPEN / DRAFT / UNMERGED and original ancestry. No workflow retry/dispatch, merge, rebase, retarget, OAuth, credentials, real media, upload, publishing, or deployment. Issue #68 remains OPEN / WAITING_FOR_OWNER_APPROVAL; live uploads/public publishing remain disabled.
